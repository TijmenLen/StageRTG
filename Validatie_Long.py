from raystation import *
import csv
import time

start_time = time.time()

# =====================================================
# SETTINGS
# =====================================================

experiments = [

    {"id": 1,  "goal": 500, "importance": 0.5,  "runs": 2, "iterations": 60},
    {"id": 2,  "goal": 500, "importance": 0.5,  "runs": 3, "iterations": 60},

    {"id": 3,  "goal": 500, "importance": 0.5,  "runs": 1, "iterations": 20},
    {"id": 4,  "goal": 800, "importance": 0.5,  "runs": 1, "iterations": 20},
    {"id": 5,  "goal": 700, "importance": 0.5,  "runs": 1, "iterations": 20},
    {"id": 6,  "goal": 600, "importance": 0.5,  "runs": 1, "iterations": 20},
    {"id": 7,  "goal": 500, "importance": 0.5,  "runs": 1, "iterations": 20},
    {"id": 8,  "goal": 400, "importance": 0.5,  "runs": 1, "iterations": 20},
    {"id": 9,  "goal": 300, "importance": 0.5,  "runs": 1, "iterations": 20},

    {"id":10, "goal":800, "importance":0.5,  "runs":1, "iterations":60},
    {"id":11, "goal":800, "importance":0.5,  "runs":2, "iterations":60},
    {"id":12, "goal":700, "importance":0.5,  "runs":1, "iterations":60},
    {"id":13, "goal":700, "importance":0.5,  "runs":2, "iterations":60},
    {"id":14, "goal":500, "importance":0.5,  "runs":2, "iterations":60},

    {"id":15, "goal":700, "importance":0.1,  "runs":1, "iterations":60},
    {"id":16, "goal":700, "importance":0.2,  "runs":1, "iterations":60},
    {"id":17, "goal":700, "importance":0.3,  "runs":1, "iterations":60},
    {"id":18, "goal":700, "importance":0.4,  "runs":1, "iterations":60},
    {"id":19, "goal":700, "importance":0.5,  "runs":1, "iterations":60},
    {"id":20, "goal":700, "importance":0.6,  "runs":1, "iterations":60},
    {"id":21, "goal":700, "importance":0.8,  "runs":1, "iterations":60},
    {"id":22, "goal":700, "importance":0.95, "runs":1, "iterations":60},

    {"id":23, "goal":700, "importance":0.8, "runs":1, "iterations":20},
    {"id":24, "goal":700, "importance":0.8, "runs":2, "iterations":20},

    {"id":25, "goal":700, "importance":0.8, "runs":1, "iterations":40},
    {"id":26, "goal":700, "importance":0.8, "runs":2, "iterations":40},

    {"id":27, "goal":700, "importance":0.8, "runs":1, "iterations":60},
    {"id":28, "goal":700, "importance":0.8, "runs":2, "iterations":60},

    {"id":29, "goal":700, "importance":0.8, "runs":2, "iterations":80},
    {"id":30, "goal":700, "importance":0.8, "runs":2, "iterations":200},

    {"id":31, "goal":700, "importance":0.8, "runs":3, "iterations":40},
    {"id":32, "goal":700, "importance":0.8, "runs":3, "iterations":80},
    {"id":33, "goal":700, "importance":0.8, "runs":3, "iterations":60}
]

test_experiments = experiments

results = []

# =====================================================
# HELPER FUNCTIONS
# =====================================================

def get_plan_metrics(plan):

    mhd = round(
        plan.TreatmentCourse.TotalDose.GetDoseStatistic(
            RoiName="Heart",
            DoseType="Average"
        ) / 100,
        2
    )

    mld = round(
        plan.TreatmentCourse.TotalDose.GetDoseStatistic(
            RoiName="_Lungs_Opti",
            DoseType="Average"
        ) / 100,
        2
    )

    return mhd, mld

# =====================================================
# CURRENT PATIENT
# =====================================================

patient = get_current("Patient")
case = get_current("Case")
starting_plan = get_current("Plan")

original_plan_name = starting_plan.Name

print("Starting plan:", original_plan_name)

# =====================================================
# LOG ORIGINAL PLAN
# =====================================================

mhd, mld = get_plan_metrics(starting_plan)

results.append({
    "Plan": "Original",
    "MHD_Gy": mhd,
    "MLD_Gy": mld
})

# =====================================================
# CREATE ALL PLANS FIRST
# =====================================================

print("")
print("Creating plan copies...")

for exp in test_experiments:

    plan_name = f"Longsparing_{exp['id']:02d}"

    try:

        case.CopyPlan(
            PlanName=original_plan_name,
            NewPlanName=plan_name,
            KeepBeamSetNames=False
        )

        print("Created:", plan_name)

    except Exception as e:

        print("Failed creating:", plan_name)
        print(e)

patient.Save()

print("")
print("All copies created.")
print("")

# =====================================================
# CONSERVATION ROIS
# =====================================================

conservation_rois = [

    case.PatientModel.RegionsOfInterest['_PTVt_Opti'],
    case.PatientModel.RegionsOfInterest['_PTVt_Opti&Lungs'],
    case.PatientModel.RegionsOfInterest['_PTVt_Opti-Lungs'],
    case.PatientModel.RegionsOfInterest['Kidney_L'],
    case.PatientModel.RegionsOfInterest['Kidney_R'],
    case.PatientModel.RegionsOfInterest['Liver'],
    case.PatientModel.RegionsOfInterest['Heart'],
    case.PatientModel.RegionsOfInterest['SpinalCord'],
    case.PatientModel.RegionsOfInterest['Spleen']

]

# =====================================================
# RUN EXPERIMENTS
# =====================================================

for exp in test_experiments:

    plan_name = f"Longsparing_{exp['id']:02d}"

    print("")
    print("===================================")
    print("Starting", plan_name)
    print("===================================")

    try:

        plan = case.TreatmentPlans[plan_name]
        plan.SetCurrent()

        plan = get_current("Plan")
        beam_set = get_current("BeamSet")

        # Add Lung clinical goal

        plan.TreatmentCourse.EvaluationSetup.AddClinicalGoal(
            RoiName="_Lungs_Opti",
            GoalCriteria="AtMost",
            GoalType="AverageDose",
            PrimaryAcceptanceLevel=exp["goal"],
            SecondaryAcceptanceLevel=None,
            ParameterValue=0,
            IsComparativeGoal=False,
            BeamSet=beam_set,
            Priority=10,
            AssociateToPlan=False
        )

        evals = plan.TreatmentCourse.EvaluationSetup.EvaluationFunctions

        lung_goal = evals[len(evals)-1]

        goals = [
		evals[0],   # PTV >98%
		evals[1],   # PTV <1%
		lung_goal
		]

        for run_nr in range(exp["runs"]):

            print(
                f"Run {run_nr + 1} / {exp['runs']}"
            )

            plan.PlanOptimizations[0].PersistFineTuningOptimizationSettings(
                ClinicalGoals=goals,
                RoiList=conservation_rois,
                OptimalityTolerance=0,
                MaxNumberOfIterations=exp["iterations"],
                ComputeIntermediateDose=False,
                ComputeFinalDose=True,
                ClinicalGoalRelativeImportance=exp["importance"],
                SpatialConservationObjectiveWeight=0.1,
                ClinicalGoalShift=1
            )

            plan.PlanOptimizations[0].RunFineTuningOptimization(
                ClinicalGoalsToExplore=goals,
                ConservationRois=conservation_rois
            )

        mhd, mld = get_plan_metrics(plan)

        results.append({
            "Plan": plan_name,
            "MHD_Gy": mhd,
            "MLD_Gy": mld
        })

        print(
            f"Completed {plan_name} | "
            f"MHD={mhd} Gy | "
            f"MLD={mld} Gy"
        )

        patient.Save()

    except Exception as e:

        print("FAILED:", plan_name)
        print(e)

# =====================================================
# EXPORT RESULTS
# =====================================================

with open(
    "LungValidationResults.csv",
    "w",
    newline=""
) as csvfile:

    writer = csv.DictWriter(
        csvfile,
        fieldnames=[
            "Plan",
            "MHD_Gy",
            "MLD_Gy"
        ]
    )

    writer.writeheader()
    writer.writerows(results)

print("")
print("Results saved to HeartValidationResults.csv")

# =====================================================
# TIMER
# =====================================================

length_seconds = round(time.time() - start_time)

minutes = length_seconds // 60
seconds = length_seconds % 60

print("")
print("Finished")

if minutes > 0:
    print(f"Runtime: {minutes} min {seconds} sec")
else:
    print(f"Runtime: {seconds} sec")