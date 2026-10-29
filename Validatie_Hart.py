from raystation import *
import csv
import time

start_time = time.time()

# =====================================================
# SETTINGS
# =====================================================

experiments = [

    {"id": 1,  "goal": 400, "importance": 0.2, "runs": 1,  "iterations": 20, "ptv98": False},
    {"id": 2,  "goal": 400, "importance": 0.5, "runs": 1,  "iterations": 20, "ptv98": False},
    {"id": 3,  "goal": 400, "importance": 0.5, "runs": 2,  "iterations": 20, "ptv98": False},
    {"id": 4,  "goal": 400, "importance": 0.5, "runs": 1,  "iterations": 40, "ptv98": False},

    {"id": 5,  "goal": 400, "importance": 0.5, "runs": 1,  "iterations": 20, "ptv98": True},
    {"id": 6,  "goal": 400, "importance": 0.5, "runs": 2,  "iterations": 20, "ptv98": True},
    {"id": 7,  "goal": 400, "importance": 0.5, "runs": 3,  "iterations": 20, "ptv98": True},
    {"id": 8,  "goal": 400, "importance": 0.5, "runs": 4,  "iterations": 20, "ptv98": True},
    {"id": 9,  "goal": 400, "importance": 0.5, "runs": 5,  "iterations": 20, "ptv98": True},
    {"id":10,  "goal": 400, "importance": 0.5, "runs": 6,  "iterations": 20, "ptv98": True},
    {"id":11,  "goal": 400, "importance": 0.5, "runs": 7,  "iterations": 20, "ptv98": True},
    {"id":12,  "goal": 400, "importance": 0.5, "runs": 8,  "iterations": 20, "ptv98": True},
    {"id":13,  "goal": 400, "importance": 0.5, "runs": 9,  "iterations": 20, "ptv98": True},
    {"id":14,  "goal": 400, "importance": 0.5, "runs":10,  "iterations": 20, "ptv98": True},

    {"id":15,  "goal": 400, "importance": 0.5, "runs": 1,  "iterations": 60, "ptv98": True},
    {"id":16,  "goal": 400, "importance": 0.5, "runs": 2,  "iterations": 60, "ptv98": True},
    {"id":17,  "goal": 400, "importance": 0.5, "runs": 3,  "iterations": 60, "ptv98": True},
    {"id":18,  "goal": 400, "importance": 0.5, "runs": 4,  "iterations": 60, "ptv98": True},

    {"id":19,  "goal": 300, "importance": 0.5, "runs": 1,  "iterations": 60, "ptv98": True},
    {"id":20,  "goal": 300, "importance": 0.5, "runs": 2,  "iterations": 60, "ptv98": True},
    {"id":21,  "goal": 300, "importance": 0.5, "runs": 3,  "iterations": 60, "ptv98": True},
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

    plan_name = f"Hartsparing_{exp['id']:02d}"

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
    case.PatientModel.RegionsOfInterest['Lung_L'],
    case.PatientModel.RegionsOfInterest['Lung_R'],
    case.PatientModel.RegionsOfInterest['Spleen']

]

# =====================================================
# RUN EXPERIMENTS
# =====================================================

for exp in test_experiments:

    plan_name = f"Hartsparing_{exp['id']:02d}"

    print("")
    print("===================================")
    print("Starting", plan_name)
    print("===================================")

    try:

        plan = case.TreatmentPlans[plan_name]
        plan.SetCurrent()

        plan = get_current("Plan")
        beam_set = get_current("BeamSet")

        # Add Heart clinical goal

        plan.TreatmentCourse.EvaluationSetup.AddClinicalGoal(
            RoiName="Heart",
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

        heart_goal = evals[len(evals)-1]

        if exp["ptv98"]:

            goals = [
                evals[0],   # PTV >98%
                evals[1],   # PTV <1%
                heart_goal
            ]

        else:

            goals = [
                evals[1],   # PTV <1%
                heart_goal
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
    "HeartValidationResults.csv",
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