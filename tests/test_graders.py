import unittest

from graders import GRADERS, grade_task1, grade_task2, grade_task3
from incidents import TICKETS
from models import IncidentAction


class GraderTests(unittest.TestCase):
    def test_all_ticket_ground_truth_scores_are_bounded(self) -> None:
        for ticket in TICKETS:
            action = IncidentAction(
                incident_id=ticket["incident_id"],
                task_type=ticket["task_type"],
                **ticket["ground_truth"],
            )
            score, reason = GRADERS[ticket["task_type"]](action, ticket["ground_truth"])
            self.assertGreaterEqual(score, 0.0, ticket["incident_id"])
            self.assertLessEqual(score, 1.0, ticket["incident_id"])
            self.assertIsInstance(reason, str)

    def test_task1_grader_supports_partial_credit(self) -> None:
        exact = IncidentAction(
            incident_id="INC-TEST-1",
            task_type="task1",
            severity="SEV1",
        )
        adjacent = IncidentAction(
            incident_id="INC-TEST-1",
            task_type="task1",
            severity="SEV2",
        )
        exact_score, _ = grade_task1(exact, {"severity": "SEV1"})
        adjacent_score, _ = grade_task1(adjacent, {"severity": "SEV1"})
        self.assertEqual(exact_score, 1.0)
        self.assertEqual(adjacent_score, 0.5)

    def test_task2_grader_is_not_constant(self) -> None:
        exact = IncidentAction(
            incident_id="INC-TEST-2",
            task_type="task2",
            root_cause="DATABASE",
        )
        fallback = IncidentAction(
            incident_id="INC-TEST-2",
            task_type="task2",
            root_cause="UNKNOWN",
        )
        wrong = IncidentAction(
            incident_id="INC-TEST-2",
            task_type="task2",
            root_cause="NETWORK",
        )
        exact_score, _ = grade_task2(exact, {"root_cause": "DATABASE"})
        fallback_score, _ = grade_task2(fallback, {"root_cause": "DATABASE"})
        wrong_score, _ = grade_task2(wrong, {"root_cause": "DATABASE"})
        self.assertEqual(exact_score, 1.0)
        self.assertEqual(fallback_score, 0.25)
        self.assertEqual(wrong_score, 0.0)

    def test_task2_grader_rewards_related_domain_partial_credit(self) -> None:
        near_miss = IncidentAction(
            incident_id="INC-TEST-2A",
            task_type="task2",
            root_cause="APPLICATION",
        )
        score, reason = grade_task2(near_miss, {"root_cause": "DATABASE"})
        self.assertEqual(score, 0.5)
        self.assertIn("partial credit", reason.lower())

    def test_task3_grader_rewards_safe_fallbacks(self) -> None:
        exact = IncidentAction(
            incident_id="INC-TEST-3",
            task_type="task3",
            action="FAILOVER",
        )
        fallback = IncidentAction(
            incident_id="INC-TEST-3",
            task_type="task3",
            action="INVESTIGATE",
        )
        wrong = IncidentAction(
            incident_id="INC-TEST-3",
            task_type="task3",
            action="NO_ACTION",
        )
        exact_score, _ = grade_task3(exact, {"action": "FAILOVER"})
        fallback_score, _ = grade_task3(fallback, {"action": "FAILOVER"})
        wrong_score, _ = grade_task3(wrong, {"action": "FAILOVER"})
        self.assertEqual(exact_score, 1.0)
        self.assertEqual(fallback_score, 0.4)
        self.assertEqual(wrong_score, 0.0)

    def test_task3_grader_rewards_related_action_partial_credit(self) -> None:
        restart_instead_of_failover = IncidentAction(
            incident_id="INC-TEST-3A",
            task_type="task3",
            action="RESTART_SERVICE",
        )
        notify_vendor_instead_of_investigate = IncidentAction(
            incident_id="INC-TEST-3B",
            task_type="task3",
            action="NOTIFY_VENDOR",
        )
        restart_score, _ = grade_task3(restart_instead_of_failover, {"action": "FAILOVER"})
        vendor_score, _ = grade_task3(notify_vendor_instead_of_investigate, {"action": "INVESTIGATE"})
        self.assertEqual(restart_score, 0.25)
        self.assertEqual(vendor_score, 0.25)


if __name__ == "__main__":
    unittest.main()
