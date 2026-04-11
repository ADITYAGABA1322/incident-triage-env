import random
import uuid

from incidents import TICKETS
from graders import GRADERS
from models import (
    IncidentAction,
    IncidentObservation,
    IncidentReward,
    IncidentState,
    RecommendedAction,
    RootCauseCategory,
    SeverityLevel,
    StepResult,
    TaskType,
)

TASK_SPECS = {
    TaskType.TASK1: {
        "name": "Severity Classification",
        "difficulty": "easy",
        "expected_field": "severity",
        "allowed_values": [item.value for item in SeverityLevel],
        "description": "Classify the severity of the incident using blast radius, user impact, and business risk.",
    },
    TaskType.TASK2: {
        "name": "Root Cause Classification",
        "difficulty": "medium",
        "expected_field": "root_cause",
        "allowed_values": [item.value for item in RootCauseCategory],
        "description": "Identify the most likely failure domain from the incident evidence.",
    },
    TaskType.TASK3: {
        "name": "Recommended Action",
        "difficulty": "hard",
        "expected_field": "action",
        "allowed_values": [item.value for item in RecommendedAction],
        "description": "Choose the best immediate operational response for stabilizing the incident.",
    },
}
TICKETS_BY_ID = {ticket["incident_id"]: ticket for ticket in TICKETS}


class IncidentEnv:

    def __init__(self):
        self.current_ticket = None
        self.episode_id = ""
        self.step_count = 0
        self.max_steps = 1
        self.total_reward = 0.0
        self.done = False
        self.last_reward = 0.0
        self.last_action_summary = None

    def reset(
        self,
        task_type: TaskType | str | None = None,
        ticket_id: str | None = None,
        seed: int | None = None,
    ) -> StepResult:
        normalized_task = TaskType(task_type) if task_type else None
        self.current_ticket = self._select_ticket(normalized_task, ticket_id, seed)
        self.episode_id = str(uuid.uuid4())
        self.step_count = 0
        self.total_reward = 0.0
        self.done = False
        self.last_reward = 0.0
        self.last_action_summary = None

        return StepResult(
            observation=self._build_observation(),
            reward=IncidentReward(value=0.0, reason="Episode initialized."),
            done=False,
            info={
                "episode_id": self.episode_id,
                "task_name": self._task_spec()["name"],
                "difficulty": self._task_spec()["difficulty"],
                "max_steps": self.max_steps,
            },
        )

    def step(self, action: IncidentAction) -> StepResult:
        if self.current_ticket is None:
            raise RuntimeError("Call reset() before step()")
        if self.done:
            raise RuntimeError("Episode already completed. Call reset() to start a new one.")

        if action.incident_id != self.current_ticket["incident_id"]:
            raise ValueError(
                f"Action incident_id '{action.incident_id}' does not match "
                f"current ticket '{self.current_ticket['incident_id']}'"
            )
        if action.task_type != TaskType(self.current_ticket["task_type"]):
            raise ValueError(
                f"Action task_type '{action.task_type.value}' does not match "
                f"current ticket task_type '{self.current_ticket['task_type']}'"
            )

        self._validate_action(action)

        task_type = self.current_ticket["task_type"]
        ground_truth = self.current_ticket["ground_truth"]
        grader_fn = GRADERS[task_type]
        reward_value, reward_reason = grader_fn(action, ground_truth)

        agent_answer = action.selected_value() or "NONE"
        selected_field = action.selected_field() or "NONE"
        ground_truth_value = list(ground_truth.values())[0]

        self.step_count += 1
        self.last_reward = reward_value
        self.total_reward += reward_value
        self.done = self.step_count >= self.max_steps
        self.last_action_summary = f"Submitted {selected_field}={agent_answer}"

        return StepResult(
            observation=self._build_observation(),
            reward=IncidentReward(value=reward_value, reason=reward_reason),
            done=self.done,
            info={
                "episode_id": self.episode_id,
                "task_name": self._task_spec()["name"],
                "difficulty": self._task_spec()["difficulty"],
                "correct": reward_value == 1.0,
                "ground_truth": ground_truth_value,
                "agent_answer": agent_answer,
                "selected_field": selected_field,
                "max_steps": self.max_steps,
            },
        )

    def state(self, session_id: str | None = None) -> IncidentState:
        if self.current_ticket is None:
            raise RuntimeError("No active episode. Call reset() first.")

        return IncidentState(
            episode_id=self.episode_id,
            session_id=session_id,
            step_count=self.step_count,
            max_steps=self.max_steps,
            total_reward=self.total_reward,
            done=self.done,
            incident_id=self.current_ticket["incident_id"],
            task_type=TaskType(self.current_ticket["task_type"]),
            difficulty=self._task_spec()["difficulty"],
            status="completed" if self.done else "awaiting_action",
            last_reward=self.last_reward,
        )

    def _select_ticket(
        self,
        task_type: TaskType | None = None,
        ticket_id: str | None = None,
        seed: int | None = None,
    ) -> dict:
        if ticket_id:
            ticket = TICKETS_BY_ID.get(ticket_id)
            if ticket is None:
                raise ValueError(f"No ticket found for ticket_id: {ticket_id}")
            if task_type and ticket["task_type"] != task_type.value:
                raise ValueError(
                    f"Ticket '{ticket_id}' belongs to task_type '{ticket['task_type']}', "
                    f"not '{task_type.value}'"
                )
            return ticket

        pool = TICKETS
        if task_type:
            pool = [ticket for ticket in TICKETS if ticket["task_type"] == task_type.value]
        if not pool:
            raise ValueError(f"No tickets found for task_type: {task_type}")

        chooser = random.Random(seed) if seed is not None else random
        return chooser.choice(pool)

    def _task_spec(self) -> dict:
        if self.current_ticket is None:
            raise RuntimeError("No active episode. Call reset() first.")
        return TASK_SPECS[TaskType(self.current_ticket["task_type"])]

    def _build_observation(self) -> IncidentObservation:
        spec = self._task_spec()
        return IncidentObservation(
            incident_id=self.current_ticket["incident_id"],
            task_type=TaskType(self.current_ticket["task_type"]),
            difficulty=spec["difficulty"],
            task_description=spec["description"],
            alert_text=self.current_ticket["alert_text"],
            context=self.current_ticket["context"],
            expected_field=spec["expected_field"],
            allowed_values=spec["allowed_values"],
            step_count=self.step_count,
            max_steps=self.max_steps,
            last_action_summary=self.last_action_summary,
            last_reward=self.last_reward,
            episode_status="completed" if self.done else "awaiting_action",
        )

    def _validate_action(self, action: IncidentAction) -> None:
        populated = action.populated_fields()
        if len(populated) != 1:
            raise ValueError("Action must populate exactly one of severity, root_cause, or action.")

        expected_field = self._task_spec()["expected_field"]
        if expected_field not in populated:
            raise ValueError(
                f"Task '{self.current_ticket['task_type']}' expects field '{expected_field}', "
                f"but got '{next(iter(populated))}'."
            )
