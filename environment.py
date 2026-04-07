#----- Edited file--------------
# environment.py

import random
from models import IncidentAction, IncidentObservation, StepResult
from incidents import TICKETS
from graders import GRADERS


class IncidentEnv:

    def __init__(self):
        self.current_ticket = None

    def reset(self, task_type: str = None) -> IncidentObservation:
        pool = TICKETS
        if task_type:
            pool = [t for t in TICKETS if t["task_type"] == task_type]
        if not pool:
            raise ValueError(f"No tickets found for task_type: {task_type}")

        self.current_ticket = random.choice(pool)

        return IncidentObservation(
            incident_id=self.current_ticket["incident_id"],
            task_type=self.current_ticket["task_type"],
            alert_text=self.current_ticket["alert_text"],
            context=self.current_ticket["context"],
        )

    def step(self, action: IncidentAction) -> StepResult:
        if self.current_ticket is None:
            raise RuntimeError("Call reset() before step()")

        if action.incident_id != self.current_ticket["incident_id"]:
            raise ValueError(
                f"Action incident_id '{action.incident_id}' does not match "
                f"current ticket '{self.current_ticket['incident_id']}'"
            )

        task_type = self.current_ticket["task_type"]
        ground_truth = self.current_ticket["ground_truth"]
        grader_fn = GRADERS[task_type]
        reward = grader_fn(action, ground_truth)

        agent_answer = (
            action.severity.value    if task_type == "task1" and action.severity   else
            action.root_cause.value  if task_type == "task2" and action.root_cause else
            action.action.value      if task_type == "task3" and action.action      else
            "NONE"
        )

        gt_field = list(ground_truth.values())[0]

        return StepResult(
            incident_id=self.current_ticket["incident_id"],
            task_type=task_type,
            reward=reward,
            correct=reward == 1.0,
            ground_truth=gt_field,
            agent_answer=agent_answer,
        )