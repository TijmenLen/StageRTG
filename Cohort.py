from raystation import *
import re
import csv

results = []

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

        # Find starting plan
        starting_plan = None

        for plan in case.TreatmentPlans:

            if (re.search(r'P\d+B\d+', plan.Name)and not plan.Name.startswith("Hartsparing_")and not plan.Name.startswith("Longsparing_")):
                starting_plan = plan
                break

        if starting_plan is None:
            print("Geen startplan gevonden voor",patient.PatientID)
            continue

        print("Startplan gevonden:",starting_plan.Name)

        starting_plan.SetCurrent()
        
        #
        # Log Data
        #

        plan = get_current("Plan")
        beam_set = get_current("BeamSet")

        mhd, mld, total_mu = get_plan_metrics(plan,beam_set)

        results.append({"LastName": patient_info["LastName"],"PlanType": "Original","MHD_Gy": mhd,"MLD_Gy": mld,"MU": total_mu})

        #
        # Create copies
        #

        heart_plan_name = (f"Hartsparing_{starting_plan.Name}")

        lung_plan_name = (f"Longsparing_{starting_plan.Name}")

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

        plan.TreatmentCourse.EvaluationSetup.AddClinicalGoal(RoiName="Heart",GoalCriteria="AtMost",GoalType="AverageDose",PrimaryAcceptanceLevel=300,SecondaryAcceptanceLevel=None,ParameterValue=0,IsComparativeGoal=False,BeamSet=beam_set,Priority=10,AssociateToPlan=False)

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

        results.append({"LastName": patient_info["LastName"],"PlanType": "Heart","MHD_Gy": mhd,"MLD_Gy": mld,"MU": total_mu})

        patient.Save()

        #
        # LUNG FINETUNING
        #

        print("Start longsparende finetuning")

        lung_plan = case.TreatmentPlans[lung_plan_name]

        lung_plan.SetCurrent()

        plan = get_current("Plan")
        beam_set = get_current("BeamSet")

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

        results.append({"LastName": patient_info["LastName"],"PlanType": "Lung","MHD_Gy": mhd,"MLD_Gy": mld,"MU": total_mu})

        patient.Save()

        print("Patiënt afgerond:",patient.PatientID)

    except Exception as e:

        print("")
        print("FOUT BIJ PATIËNT:",patient_info["LastName"])
        print(e)

        continue

with open("Heart_Lung_Results.csv","w",newline="") as csvfile:

    writer = csv.DictWriter(csvfile,fieldnames=["LastName","PlanType","MHD_Gy","MLD_Gy","MU"])

    writer.writeheader()
    writer.writerows(results)

print("Resultaten opgeslagen in Heart_Lung_Results.csv")