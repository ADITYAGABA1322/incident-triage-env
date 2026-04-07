#----- Edited file--------------
# graders.py

from models import IncidentAction

_SEV_ORDER = {"SEV1": 0, "SEV2": 1, "SEV3": 2}

def grade_task1(action: IncidentAction, ground_truth: dict) -> float:
    if action.severity is None:
        return 0.0
    predicted = _SEV_ORDER.get(action.severity.value, -1)
    expected  = _SEV_ORDER.get(ground_truth["severity"], -1)
    distance  = abs(predicted - expected)
    return {0: 1.0, 1: 0.5, 2: 0.0}[distance]


def grade_task2(action: IncidentAction, ground_truth: dict) -> float:
    if action.root_cause is None:
        return 0.0
    return 1.0 if action.root_cause.value == ground_truth["root_cause"] else 0.0


def grade_task3(action: IncidentAction, ground_truth: dict) -> float:
    if action.action is None:
        return 0.0
    return 1.0 if action.action.value == ground_truth["action"] else 0.0


GRADERS = {
    "task1": grade_task1,
    "task2": grade_task2,
    "task3": grade_task3,
}