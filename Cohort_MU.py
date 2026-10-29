from raystation import *
import re
import csv

all_results = []
pxbx_results = []
declined_results = []

def get_plan_metrics(plan, beam_set):

    mhd = round(plan.TreatmentCourse.TotalDose.GetDoseStatistic(RoiName="Heart",DoseType="Average") / 100,2)

    mld = round(plan.TreatmentCourse.TotalDose.GetDoseStatistic(RoiName="_Lungs_Opti",DoseType="Average") / 100,2)

    total_mu = round(sum(beam.BeamMU for beam in beam_set.Beams),2)

    return mhd, mld, total_mu


# Number of finetuning runs
n_runs = 3

# Get patient database
patient_db = get_current("PatientDB")

# Find cohort
cohort = patient_db.QueryPatientInfo(Filter={"LastName": "Oes_23"})

cohort = [patient_info for patient_info in cohort if "1_1" not in patient_info["LastName"]]

print("Aantal patiënten gevonden:", len(cohort))

for patient_info in cohort:

    try:

        print("")
        print("========================================")
        print("Start patiënt:", patient_info["LastName"])

        # Load patient
        patient = patient_db.LoadPatient(PatientInfo=patient_info)

        # Select case
        case = patient.Cases[0]
        case.SetCurrent()

        # Find all relevant starting plans

        starting_plans = []

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

            is_generated = (
                plan.Name.startswith("Hartsparing_")
                or plan.Name.startswith("Longsparing_")
            )

            if not is_generated and (is_pxbx or is_declined):

                if is_pxbx:
                    source_type = "PxBx"
                else:
                    source_type = "Declined"

                starting_plans.append(
                    (plan, source_type)
                )

        if len(starting_plans) == 0:

            print(
                "Geen startplannen gevonden voor",
                patient.PatientID
            )

            continue

        print(
            "Aantal startplannen gevonden:",
            len(starting_plans)
        )

        for starting_plan, source_type in starting_plans:

            print("")
            print("----------------------------------------")
            print(
                "Startplan:",
                starting_plan.Name,
                "(" + source_type + ")"
            )

            starting_plan.SetCurrent()

            #
            # Log Data
            #

            plan = get_current("Plan")
            beam_set = get_current("BeamSet")

            mhd, mld, total_mu = get_plan_metrics(
                plan,
                beam_set
            )

            row={
                "LastName": patient_info["LastName"],
                "SourceType": source_type,
                "PlanName": starting_plan.Name,
                "PlanType": "Original",
                "MHD_Gy": mhd,
                "MLD_Gy": mld,
                "MU": total_mu}
            
            all_results.append(row)

            if source_type == "PxBx":
                pxbx_results.append(row)

            else:
                declined_results.append(row)

            #
            # Create copies
            #

            heart_plan_name = (f"Hartsparing_{starting_plan.Name}")

            lung_plan_name = (f"Longsparing_{starting_plan.Name}")
            
            existing_plan_names = [
            p.Name
            for p in case.TreatmentPlans
            ]

            if heart_plan_name in existing_plan_names:
                print("Bestaat al:", heart_plan_name)
                continue

            if lung_plan_name in existing_plan_names:
                print("Bestaat al:", lung_plan_name)
                continue

            print("Maken van Hartsparend plan...")

            case.CopyPlan(PlanName=starting_plan.Name,NewPlanName=heart_plan_name,KeepBeamSetNames=False)

            print("Maken van Longsparend plan...")

            case.CopyPlan(PlanName=starting_plan.Name,NewPlanName=lung_plan_name,KeepBeamSetNames=False)

            patient.Save()

            #
            # HEART FINETUNING
            #

            print("Start hartsparende finetuning")

            heart_plan = case.TreatmentPlans[heart_plan_name]

            heart_plan.SetCurrent()

            plan = get_current("Plan")
            beam_set = get_current("BeamSet")

            beam_settings = (
            plan.PlanOptimizations[0]
            .OptimizationParameters
            .TreatmentSetupSettings[0]
            .BeamSettings
            )

            n_beams = len(beam_settings)

            mu_per_beam = 150 / n_beams

            print(f"Aantal beams: {n_beams}")
            print(f"MU per beam: {mu_per_beam}")

            for beam in beam_settings:

                arc = beam.ArcConversionPropertiesPerBeam

                beam.ArcConversionPropertiesPerBeam.EditArcBasedBeamOptimizationSettings(
                    CreateDualArcs=(arc.NumberOfArcs == 2),
                    FinalGantrySpacing=arc.FinalArcGantrySpacing,
                    MaxArcDeliveryTime=arc.MaxArcDeliveryTime,
                    BurstGantrySpacing=arc.BurstGantrySpacing,
                    MaxArcMU=mu_per_beam
                )

            plan.TreatmentCourse.EvaluationSetup.AddClinicalGoal(RoiName="Heart",GoalCriteria="AtMost",GoalType="AverageDose",PrimaryAcceptanceLevel=200,SecondaryAcceptanceLevel=None,ParameterValue=0,IsComparativeGoal=False,BeamSet=beam_set,Priority=10,AssociateToPlan=False)

            for i in range(n_runs):

                print("Hart run",i + 1,"van",n_runs)

                plan.PlanOptimizations[0].PersistFineTuningOptimizationSettings(ClinicalGoals=[plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[0],plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[1],plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[len(plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions)-1]],RoiList=[case.PatientModel.RegionsOfInterest['_PTVt_Opti'],case.PatientModel.RegionsOfInterest['_PTVt_Opti&Lungs'],case.PatientModel.RegionsOfInterest['_PTVt_Opti-Lungs'],case.PatientModel.RegionsOfInterest['Kidney_L'],case.PatientModel.RegionsOfInterest['Kidney_R'],case.PatientModel.RegionsOfInterest['Liver'],case.PatientModel.RegionsOfInterest['Lung_L'],case.PatientModel.RegionsOfInterest['Lung_R'],case.PatientModel.RegionsOfInterest['Spleen']],OptimalityTolerance=0,MaxNumberOfIterations=60,ComputeIntermediateDose=False,ComputeFinalDose=True,ClinicalGoalRelativeImportance=0.5,SpatialConservationObjectiveWeight=0.1,ClinicalGoalShift=1)

                plan.PlanOptimizations[0].RunFineTuningOptimization(ClinicalGoalsToExplore=[plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[0],plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[1],plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[len(plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions)-1]],ConservationRois=[case.PatientModel.RegionsOfInterest['_PTVt_Opti'],case.PatientModel.RegionsOfInterest['_PTVt_Opti&Lungs'],case.PatientModel.RegionsOfInterest['_PTVt_Opti-Lungs'],case.PatientModel.RegionsOfInterest['Kidney_L'],case.PatientModel.RegionsOfInterest['Kidney_R'],case.PatientModel.RegionsOfInterest['Liver'],case.PatientModel.RegionsOfInterest['Lung_L'],case.PatientModel.RegionsOfInterest['Lung_R'],case.PatientModel.RegionsOfInterest['Spleen']])

            print("Hartsparend plan afgerond")

            #
            # Log Data
            #

            plan = get_current("Plan")
            beam_set = get_current("BeamSet")

            mhd, mld, total_mu = get_plan_metrics(plan,beam_set)

            row={
                "LastName": patient_info["LastName"],
                "SourceType": source_type,
                "PlanName": starting_plan.Name,
                "PlanType": "Heart",
                "MHD_Gy": mhd,
                "MLD_Gy": mld,
                "MU": total_mu}
            
            all_results.append(row)

            if source_type == "PxBx":
                pxbx_results.append(row)

            else:
                declined_results.append(row)

            patient.Save()

            #
            # LUNG FINETUNING
            #

            print("Start longsparende finetuning")

            lung_plan = case.TreatmentPlans[lung_plan_name]

            lung_plan.SetCurrent()

            plan = get_current("Plan")
            beam_set = get_current("BeamSet")

            beam_settings = (
            plan.PlanOptimizations[0]
            .OptimizationParameters
            .TreatmentSetupSettings[0]
            .BeamSettings
            )

            n_beams = len(beam_settings)

            mu_per_beam = 350 / n_beams

            print(f"Aantal beams: {n_beams}")
            print(f"MU per beam: {mu_per_beam}")

            for beam in beam_settings:

                arc = beam.ArcConversionPropertiesPerBeam

                beam.ArcConversionPropertiesPerBeam.EditArcBasedBeamOptimizationSettings(
                    CreateDualArcs=(arc.NumberOfArcs == 2),
                    FinalGantrySpacing=arc.FinalArcGantrySpacing,
                    MaxArcDeliveryTime=arc.MaxArcDeliveryTime,
                    BurstGantrySpacing=arc.BurstGantrySpacing,
                    MaxArcMU=mu_per_beam
                )

            plan.TreatmentCourse.EvaluationSetup.AddClinicalGoal(RoiName="_Lungs_Opti",GoalCriteria="AtMost",GoalType="AverageDose",PrimaryAcceptanceLevel=700,SecondaryAcceptanceLevel=None,ParameterValue=0,IsComparativeGoal=False,BeamSet=beam_set,Priority=10,AssociateToPlan=False)

            for i in range(n_runs):

                print("Long run",i + 1,"van",n_runs)

                plan.PlanOptimizations[0].PersistFineTuningOptimizationSettings(ClinicalGoals=[plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[0],plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[1],plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[len(plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions)-1]],RoiList=[case.PatientModel.RegionsOfInterest['_PTVt_Opti'],case.PatientModel.RegionsOfInterest['_PTVt_Opti&Lungs'],case.PatientModel.RegionsOfInterest['_PTVt_Opti-Lungs'],case.PatientModel.RegionsOfInterest['Heart'],case.PatientModel.RegionsOfInterest['Kidney_L'],case.PatientModel.RegionsOfInterest['Kidney_R'],case.PatientModel.RegionsOfInterest['Liver'],case.PatientModel.RegionsOfInterest['SpinalCord'],case.PatientModel.RegionsOfInterest['Spleen']],OptimalityTolerance=0,MaxNumberOfIterations=60,ComputeIntermediateDose=False,ComputeFinalDose=True,ClinicalGoalRelativeImportance=0.8,SpatialConservationObjectiveWeight=0.1,ClinicalGoalShift=1)

                plan.PlanOptimizations[0].RunFineTuningOptimization(ClinicalGoalsToExplore=[plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[0],plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[1],plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[len(plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions)-1]],ConservationRois=[case.PatientModel.RegionsOfInterest['_PTVt_Opti'],case.PatientModel.RegionsOfInterest['_PTVt_Opti&Lungs'],case.PatientModel.RegionsOfInterest['_PTVt_Opti-Lungs'],case.PatientModel.RegionsOfInterest['Heart'],case.PatientModel.RegionsOfInterest['Kidney_L'],case.PatientModel.RegionsOfInterest['Kidney_R'],case.PatientModel.RegionsOfInterest['Liver'],case.PatientModel.RegionsOfInterest['SpinalCord'],case.PatientModel.RegionsOfInterest['Spleen']])

            print("Longsparend plan afgerond")
            
            #
            # Log Data
            #

            plan = get_current("Plan")
            beam_set = get_current("BeamSet")

            mhd, mld, total_mu = get_plan_metrics(plan,beam_set)

            row={
                "LastName": patient_info["LastName"],
                "SourceType": source_type,
                "PlanName": starting_plan.Name,
                "PlanType": "Lung",
                "MHD_Gy": mhd,
                "MLD_Gy": mld,
                "MU": total_mu}
            
            all_results.append(row)

            if source_type == "PxBx":
                pxbx_results.append(row)

            else:
                declined_results.append(row)

            patient.Save()

            print("Patiënt afgerond:",patient.PatientID)

    except Exception as e:

        print("")
        print("FOUT BIJ PATIËNT:",patient_info["LastName"])
        print(e)

        continue

def write_csv(filename, data):

    if len(data) == 0:
        return

    with open(
        filename,
        "w",
        newline=""
    ) as csvfile:

        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "LastName",
                "PlanName",
                "SourceType",
                "PlanType",
                "MHD_Gy",
                "MLD_Gy",
                "MU"
            ]
        )

        writer.writeheader()
        writer.writerows(data)


write_csv(
    "all_plans.csv",
    all_results
)

write_csv(
    "pxbx_plans.csv",
    pxbx_results
)

write_csv(
    "declined_plans.csv",
    declined_results
)

print("")
print("========================================")
print("SCRIPT VOLTOOID")
print("========================================")
print("Totaal:", len(all_results))
print("PxBx:", len(pxbx_results))
print("Declined:", len(declined_results))
print("========================================")