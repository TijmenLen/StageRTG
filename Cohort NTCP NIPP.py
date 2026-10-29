from raystation import *
import re
import csv
import math
import os

# ============================================================
# CONFIGURATION
# ============================================================

COHORT_NAME = "Oes_23"

HEART = "Heart"

ALL_CSV = r"all_plans_LIPP.csv"
PXBX_CSV = r"pxbx_plans_LIPP.csv"
DECLINED_CSV = r"declined_plans_LIPP.csv"

PATIENT_DATA_CSV = r"patient_data.csv"

# ============================================================
# NTCP MODEL
# LP = -3.0352 + 0.1*sqrt(GTV) + 0.4457*sqrt(MHD)
# NTCP = 1/(1+exp(-LP))
# ============================================================

class MortalityNTCP:

    def __init__(self):

        self.intercept = -3.0352
        self.gtv_coef = 0.1000
        self.mhd_coef = 0.4457

    def predict(self, gtv, mhd):

        lp = (
            self.intercept
            + self.gtv_coef * math.sqrt(gtv)
            + self.mhd_coef * math.sqrt(mhd)
        )

        ntcp = 1.0 / (
            1.0 + math.exp(-lp)
        )

        return ntcp, lp

# ============================================================
# LOAD GTV DATA
# ============================================================

def load_patient_data(csv_path):

    patient_data = {}

    with open(csv_path, newline="") as f:

        reader = csv.DictReader(f)

        for row in reader:

            patient_id = row["patient_id"].strip()

            patient_data[patient_id] = {
                "gtv": float(row["gtv"])
            }

    return patient_data

# ============================================================
# GET GTV + MHD
# ============================================================

def get_ntcp_data(
        patient,
        plan,
        patient_data,
        heart_name):

    patient_id = str(patient.PatientID)

    if patient_id not in patient_data:

        raise ValueError(
            "Patient '{}' not found in patient_data.csv".format(
                patient_id
            )
        )

    gtv = patient_data[patient_id]["gtv"]

    mhd_cgy = (
        plan.TreatmentCourse.TotalDose
        .GetDoseStatistic(
            RoiName=heart_name,
            DoseType="Average"
        )
    )

    mhd = mhd_cgy / 100.0

    return gtv, mhd

# ============================================================
# CSV EXPORT
# ============================================================

def write_csv(filename, data):

    if len(data) == 0:

        print("Geen data voor:", filename)
        return

    fieldnames = list(data[0].keys())

    with open(
            filename,
            "w",
            newline=""
    ) as csvfile:

        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for row in data:

            writer.writerow(row)

    print("CSV opgeslagen:", filename)

# ============================================================
# RESULTS STORAGE
# ============================================================

all_results = []
pxbx_results = []
declined_results = []

# ============================================================
# LOAD NTCP MODEL
# ============================================================

ntcp_model = MortalityNTCP()

# ============================================================
# LOAD PATIENT DATA
# ============================================================

patient_data = load_patient_data(
    os.path.join(
        os.path.dirname(__file__),
        PATIENT_DATA_CSV
    )
)

print(
    "Aantal patiënten in patient_data.csv:",
    len(patient_data)
)

# ============================================================
# GET PATIENT DATABASE
# ============================================================

patient_db = get_current("PatientDB")

cohort = patient_db.QueryPatientInfo(
    Filter={"LastName": COHORT_NAME}
)

cohort = [patient_info for patient_info in cohort if "1_1" not in patient_info["LastName"]]

print(
    "Aantal patiënten gevonden:",
    len(cohort)
)

# ============================================================
# COHORT LOOP
# ============================================================

for patient_info in cohort:

    try:

        print("")
        print("================================================")
        print(
            "Start patiënt:",
            patient_info["LastName"]
        )

        patient = patient_db.LoadPatient(
            PatientInfo=patient_info
        )

        case = patient.Cases[0]

        case.SetCurrent()

        matching_plans = []

        # ----------------------------------------------------
        # FIND RELEVANT PLANS
        # ----------------------------------------------------

        for plan in case.TreatmentPlans:

            is_pxbx = re.search(
                r'P\d+B\d+',
                plan.Name,
                re.IGNORECASE
            )

            is_declined = re.search(
                r'declined',
                plan.Name,
                re.IGNORECASE
            )

            if is_pxbx:

                matching_plans.append(
                    (plan, "PxBx")
                )

            elif is_declined:

                matching_plans.append(
                    (plan, "Declined")
                )

        print(
            "Aantal relevante plannen gevonden:",
            len(matching_plans)
        )

        # ----------------------------------------------------
        # PROCESS EACH PLAN
        # ----------------------------------------------------

        for plan, plan_type in matching_plans:

            try:
                plan.SetCurrent()

                roi_names = [
                    roi.Name
                    for roi in case.PatientModel.RegionsOfInterest
                ]

                if HEART not in roi_names:

                    raise ValueError(
                        "ROI '{}' not found".format(
                            HEART
                        )
                    )

                # ============================================
                # EXTRACT INPUT DATA
                # ============================================

                gtv, mhd = get_ntcp_data(
                    patient=patient,
                    plan=plan,
                    patient_data=patient_data,
                    heart_name=HEART
                )

                # ============================================
                # CALCULATE NTCP
                # ============================================

                ntcp, lp = ntcp_model.predict(
                    gtv,
                    mhd
                )

                # ============================================
                # STORE RESULTS
                # ============================================

                result = {
                    "PatientName":
                        patient_info["LastName"],

                    "PlanName":
                        plan.Name,

                    "PlanType":
                        plan_type,

                    "GTV":
                        round(
                            gtv,
                            2
                        ),

                    "MHD":
                        round(
                            mhd,
                            2
                        ),

                    "LP":
                        round(
                            lp,
                            6
                        ),

                    "NTCP":
                        round(
                            ntcp,
                            6
                        ),

                    "NTCP_percent":
                        round(
                            ntcp * 100.0,
                            2
                        )
                }

                all_results.append(
                    result
                )

                if plan_type == "PxBx":

                    pxbx_results.append(
                        result
                    )

                elif plan_type == "Declined":

                    declined_results.append(
                        result
                    )

            except Exception as e:

                print("")
                print("FOUT BIJ PLAN:")
                print(patient.PatientID)
                print(plan.Name)
                print(e)

                continue

        patient.Save()

        print(
            "Patiënt afgerond:",
            patient.PatientID
        )

    except Exception as e:

        print("")
        print("FOUT BIJ PATIËNT:")
        print(
            patient_info["LastName"]
        )
        print(e)

        continue

# ============================================================
# WRITE CSV FILES
# ============================================================

write_csv(
    ALL_CSV,
    all_results
)

write_csv(
    PXBX_CSV,
    pxbx_results
)

write_csv(
    DECLINED_CSV,
    declined_results
)

# ============================================================
# SUMMARY
# ============================================================

print("")
print("========================================")
print("SCRIPT VOLTOOID")
print("========================================")
print(
    "Totaal plannen:",
    len(all_results)
)
print(
    "PxBx plannen:",
    len(pxbx_results)
)
print(
    "Declined plannen:",
    len(declined_results)
)
print("========================================")