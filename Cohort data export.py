from raystation import *
import re
import csv

# ============================================================
# CONFIGURATION
# ============================================================

COHORT_NAME = "Oes_23"

HEART_ROI = "Heart"
LUNG_ROI = "_Lungs_Opti"

OUTPUT_CSV = "all_plan_data.csv"

# ============================================================
# HELPERS
# ============================================================

def safe_float(value):
    try:
        return float(value)
    except:
        return None

def excel_value(value):

    if value is None:
        return None

    if isinstance(
        value,
        (str, int, float, bool)
    ):
        return value

    try:
        return float(value)

    except:
        return str(value)

def get_mean_dose(plan, roi_name):
    try:
        return round(
            plan.TreatmentCourse.TotalDose.GetDoseStatistic(
                RoiName=roi_name,
                DoseType="Average"
            ) / 100.0,
            2
        )
    except:
        return None


def get_total_mu(beam_set):
    try:
        return round(
            sum(beam.BeamMU for beam in beam_set.Beams),
            2
        )
    except:
        return None


def get_v1_v40(plan, roi_name, prefix):

    result = {}

    dose_values = list(
        range(100, 4001, 100)
    )

    values = (
        plan.TreatmentCourse.TotalDose
        .GetRelativeVolumeAtDoseValues(
            RoiName=roi_name,
            DoseValues=dose_values
        )
    )

    for dose_gy, volume in zip(
        range(1, 41),
        values
    ):
        result[
            "{}_V{}".format(
                prefix,
                dose_gy
            )
        ] = volume

    return result


def get_goal_attribute(function, attribute_name):
    planning_goal = getattr(function, "PlanningGoal", None)

    value = getattr(
        planning_goal,
        attribute_name,
        None
    )

    if value is None:
        value = getattr(
            function,
            attribute_name,
            None
        )

    return value


def get_goal_roi_name(function):

    roi = getattr(
        function,
        "ForRegionOfInterest",
        None
    )

    roi_name = getattr(
        roi,
        "Name",
        None
    )

    if not roi_name:

        roi = getattr(
            function,
            "ForRoi",
            None
        )

        roi_name = getattr(
            roi,
            "Name",
            None
        )

    return str(roi_name or "")


def sanitize_column_name(text):

    text = str(text)

    replacements = [
        (" ", "_"),
        ("(", ""),
        (")", ""),
        ("/", "_"),
        ("\\", "_"),
        ("-", "_"),
        (":", "_")
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    return text


def collect_clinical_goals(plan):

    result = {}

    evaluation_functions = (
        plan.TreatmentCourse
        .EvaluationSetup
        .EvaluationFunctions
    )

    for function in evaluation_functions:

        roi_name = get_goal_roi_name(function)

        planning_goal = getattr(
            function,
            "PlanningGoal",
            None
        )

        goal_type = getattr(
            planning_goal,
            "Type",
            None
        )

        if goal_type is None:
            goal_type = getattr(
                planning_goal,
                "GoalType",
                None
            )

        goal_criteria = get_goal_attribute(
            function,
            "GoalCriteria"
        )

        parameter_value = get_goal_attribute(
            function,
            "ParameterValue"
        )

        goal_name = sanitize_column_name(
            "{}_{}_{}_{}".format(
                roi_name,
                goal_type,
                goal_criteria,
                parameter_value
            )
        )

        try:
            goal_value = excel_value(function.GetClinicalGoalValue())
        except:
            goal_value = None

        try:
            goal_passed = bool(
                function.EvaluateClinicalGoal()
            )
        except:
            goal_passed = None

        result[goal_name + "_Value"] = goal_value
        result[goal_name + "_Passed"] = goal_passed

    return result


def classify_plan(plan_name):

    lower = plan_name.lower()

    source_type = None

    if re.search(r'P\d+B\d+', plan_name, re.IGNORECASE):
        source_type = "Final"

    elif "declined" in lower:
        source_type = "Declined"

    else:
        return None, None

    if lower.startswith("hartsparing_"):
        plan_type = "Heart"

    elif lower.startswith("longsparing_"):
        plan_type = "Lung"

    else:
        plan_type = "Start"

    return source_type, plan_type


# ============================================================
# MAIN
# ============================================================

all_rows = []

patient_db = get_current("PatientDB")

cohort = patient_db.QueryPatientInfo(
    Filter={"LastName": COHORT_NAME}
)

cohort = [
    patient_info
    for patient_info in cohort
    if "1_1" not in patient_info["LastName"]
]

print("Aantal patiënten:", len(cohort))

for patient_info in cohort:

    try:

        print("")
        print("================================")
        print(patient_info["LastName"])

        patient = patient_db.LoadPatient(
            PatientInfo=patient_info
        )

        case = patient.Cases[0]

        case.SetCurrent()

        roi_names = [
            roi.Name
            for roi in case.PatientModel.RegionsOfInterest
        ]

        if HEART_ROI not in roi_names:
            print("Heart ROI missing")
            continue

        if LUNG_ROI not in roi_names:
            print("Lung ROI missing")
            continue

        print("Plans in case:",len(case.TreatmentPlans))

        for plan in case.TreatmentPlans:

            source_type, plan_type = classify_plan(
                plan.Name
            )

            if source_type is None:
                continue
                
            print("Processing:", plan.Name, source_type, plan_type)

            plan.SetCurrent()
            
            print("Clinical goals found:", len(plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions))

            try:
                approval_status = (
                    plan.Review.ApprovalStatus
                )
            except:
                approval_status = None

            beam_set = plan.BeamSets[0]

            row = {}

            row["LastName"] = patient_info["LastName"]

            row["PlanName"] = plan.Name

            row["SourceType"] = source_type
            row["PlanType"] = plan_type
            row["ApprovalStatus"] = approval_status

            # -----------------------------
            # MHD / MLD
            # -----------------------------

            row["MHD_Gy"] = get_mean_dose(
                plan,
                HEART_ROI
            )

            row["MLD_Gy"] = get_mean_dose(
                plan,
                LUNG_ROI
            )

            # -----------------------------
            # MU
            # -----------------------------

            row["MU"] = get_total_mu(
                beam_set
            )

            # -----------------------------
            # Heart V1-40
            # -----------------------------

            row.update(
                get_v1_v40(
                    plan,
                    HEART_ROI,
                    "Heart"
                )
            )

            # -----------------------------
            # Lung V1-40
            # -----------------------------

            row.update(
                get_v1_v40(
                    plan,
                    LUNG_ROI,
                    "Lung"
                )
            )

            # -----------------------------
            # Clinical goals
            # -----------------------------

            row.update(
                collect_clinical_goals(
                    plan
                )
            )

            all_rows.append(row)
            
            print("Exported:", plan.Name)

        patient.Save()

    except Exception as e:

        print("")
        print("FOUT BIJ PATIËNT")
        print(patient_info["LastName"])
        print(e)

# ============================================================
# WRITE CSV
# ============================================================

if len(all_rows) > 0:

    fieldnames = []

    for row in all_rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with open(
        OUTPUT_CSV,
        "w",
        newline=""
    ) as csvfile:

        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for row in all_rows:
            writer.writerow(row)

print("")
print("================================")
print("SCRIPT COMPLETE")
print("Plans exported:", len(all_rows))
print("================================")