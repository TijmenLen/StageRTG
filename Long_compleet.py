# Longsparend plan
from raystation import *

# Huidige gegevens openstaande plan
patient = get_current("Patient")
case = get_current("Case")
plan = get_current("Plan")

# Naam openstaande plan
original_plan_name = plan.Name

# Naam nieuwe plan
new_plan_name = f"Longsparing_{original_plan_name}"

# Kopieer plan
case.CopyPlan(PlanName=original_plan_name, NewPlanName=new_plan_name, KeepBeamSetNames=False)

# Opslaan openstaande plan
patient.Save()

# Open gekopieerde plan
new_plan = case.TreatmentPlans[new_plan_name]
new_plan.SetCurrent()

plan = get_current("Plan")
beam_set = get_current("BeamSet")

beam_settings = (
plan.PlanOptimizations[0]
.OptimizationParameters
.TreatmentSetupSettings[0]
.BeamSettings
)

# MU limiet instellen
n_beams = len(beam_settings)

mu_per_beam = 350 / n_beams

for beam in beam_settings:

    arc = beam.ArcConversionPropertiesPerBeam

    beam.ArcConversionPropertiesPerBeam.EditArcBasedBeamOptimizationSettings(
        CreateDualArcs=(arc.NumberOfArcs == 2),
        FinalGantrySpacing=arc.FinalArcGantrySpacing,
        MaxArcDeliveryTime=arc.MaxArcDeliveryTime,
        BurstGantrySpacing=arc.BurstGantrySpacing,
        MaxArcMU=mu_per_beam
    )

# Aantal runs iteraties
n_runs = 3

# Clinical Goal toevoegen
plan.TreatmentCourse.EvaluationSetup.AddClinicalGoal(RoiName="_Lungs_Opti",GoalCriteria="AtMost",GoalType="AverageDose",PrimaryAcceptanceLevel=700,SecondaryAcceptanceLevel=None,ParameterValue=0,IsComparativeGoal=False,BeamSet=beam_set,Priority=10,AssociateToPlan=False)
print("Clinical Goal toegevoegd")

# Finetune loop
for i in range(n_runs):

    print("Long run",i + 1,"van",n_runs)

    plan.PlanOptimizations[0].PersistFineTuningOptimizationSettings(ClinicalGoals=[plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[0],plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[1],plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[len(plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions)-1]],RoiList=[case.PatientModel.RegionsOfInterest['_PTVt_Opti'],case.PatientModel.RegionsOfInterest['_PTVt_Opti&Lungs'],case.PatientModel.RegionsOfInterest['_PTVt_Opti-Lungs'],case.PatientModel.RegionsOfInterest['Heart'],case.PatientModel.RegionsOfInterest['Kidney_L'],case.PatientModel.RegionsOfInterest['Kidney_R'],case.PatientModel.RegionsOfInterest['Liver'],case.PatientModel.RegionsOfInterest['SpinalCord'],case.PatientModel.RegionsOfInterest['Spleen']],OptimalityTolerance=0,MaxNumberOfIterations=60,ComputeIntermediateDose=False,ComputeFinalDose=True,ClinicalGoalRelativeImportance=0.8,SpatialConservationObjectiveWeight=0.1,ClinicalGoalShift=1)

    plan.PlanOptimizations[0].RunFineTuningOptimization(ClinicalGoalsToExplore=[plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[0],plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[1],plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions[len(plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions)-1]],ConservationRois=[case.PatientModel.RegionsOfInterest['_PTVt_Opti'],case.PatientModel.RegionsOfInterest['_PTVt_Opti&Lungs'],case.PatientModel.RegionsOfInterest['_PTVt_Opti-Lungs'],case.PatientModel.RegionsOfInterest['Heart'],case.PatientModel.RegionsOfInterest['Kidney_L'],case.PatientModel.RegionsOfInterest['Kidney_R'],case.PatientModel.RegionsOfInterest['Liver'],case.PatientModel.RegionsOfInterest['SpinalCord'],case.PatientModel.RegionsOfInterest['Spleen']])

print("Longsparend plan afgerond")