import json
import tempfile
import unittest
from pathlib import Path

from inference import normalize_action, write_results


class InferenceOutputTests(unittest.TestCase):
    def test_normalize_action_uppercases_model_outputs(self) -> None:
        normalized = normalize_action(
            {"action": "failover"},
            {"incident_id": "INC-014", "task_type": "task3"},
        )

        self.assertEqual(normalized["action"], "FAILOVER")
        self.assertIsNone(normalized["severity"])
        self.assertIsNone(normalized["root_cause"])

    def test_write_results_writes_summary_to_configured_path(self) -> None:
        results = [
            {"incident_id": "INC-001", "task_type": "task1", "score": 1.0, "success": True},
            {"incident_id": "INC-002", "task_type": "task2", "score": 0.5, "success": False},
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "nested" / "baseline_scores.json"
            write_results(results, output_path=output_path)

            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text())
            self.assertEqual(payload["episodes"], 2)
            self.assertAlmostEqual(payload["average_score"], 0.75)
            self.assertEqual(payload["by_task"]["task1"]["average_score"], 1.0)
            self.assertEqual(payload["by_task"]["task2"]["average_score"], 0.5)

    def test_write_results_tolerates_unwritable_path(self) -> None:
        results = [
            {"incident_id": "INC-001", "task_type": "task1", "score": 1.0, "success": True},
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            blocked_parent = Path(temp_dir) / "blocked"
            blocked_parent.write_text("not-a-directory")
            blocked_path = blocked_parent / "baseline_scores.json"

            write_results(results, output_path=blocked_path)


if __name__ == "__main__":
    unittest.main()
