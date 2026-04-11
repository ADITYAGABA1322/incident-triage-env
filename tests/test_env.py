import unittest

from fastapi.testclient import TestClient

from app import app, sessions


class IncidentEnvApiTests(unittest.TestCase):
    def setUp(self) -> None:
        sessions.clear()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        sessions.clear()

    def test_health_schema_and_mcp_helper_endpoints(self) -> None:
        health_response = self.client.get("/health")
        self.assertEqual(health_response.status_code, 200)
        self.assertEqual(health_response.json()["status"], "healthy")

        schema_response = self.client.get("/schema")
        self.assertEqual(schema_response.status_code, 200)
        schema_body = schema_response.json()
        self.assertIn("action", schema_body)
        self.assertIn("observation", schema_body)
        self.assertIn("state", schema_body)

        mcp_response = self.client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
        self.assertEqual(mcp_response.status_code, 200)
        mcp_body = mcp_response.json()
        self.assertEqual(mcp_body["jsonrpc"], "2.0")
        self.assertEqual(mcp_body["id"], 1)

    def test_tickets_endpoint_returns_safe_ticket_inventory(self) -> None:
        response = self.client.get("/tickets")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 36)
        self.assertEqual(body["tickets"][0]["incident_id"], "INC-001")
        self.assertIn("expected_field", body["tickets"][0])
        self.assertNotIn("ground_truth", body["tickets"][0])

    def test_ui_routes_and_assets_are_served(self) -> None:
        home_response = self.client.get("/")
        self.assertEqual(home_response.status_code, 200)
        self.assertIn("Incident Triage Environment", home_response.text)

        status_response = self.client.get("/status")
        self.assertEqual(status_response.status_code, 200)
        self.assertIn("Environment readiness dashboard", status_response.text)

        playground_response = self.client.get("/playground")
        self.assertEqual(playground_response.status_code, 200)
        self.assertIn("Interactive playground", playground_response.text)

        asset_response = self.client.get("/assets/app.js")
        self.assertEqual(asset_response.status_code, 200)
        self.assertIn("bootstrap", asset_response.text)

    def test_reset_returns_requested_ticket_and_session_state(self) -> None:
        response = self.client.post(
            "/reset",
            json={"task_type": "task3", "ticket_id": "INC-014"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["observation"]["incident_id"], "INC-014")
        self.assertEqual(body["observation"]["task_type"], "task3")
        self.assertEqual(body["reward"]["value"], 0.0)
        self.assertFalse(body["done"])
        self.assertIn("session_id", body["info"])
        self.assertEqual(body["info"]["state"]["status"], "awaiting_action")

    def test_step_completes_episode_and_state_endpoint_reflects_completion(self) -> None:
        reset_response = self.client.post(
            "/reset",
            json={"task_type": "task3", "ticket_id": "INC-014"},
        )
        session_id = reset_response.json()["info"]["session_id"]

        step_response = self.client.post(
            f"/step?session_id={session_id}",
            json={
                "incident_id": "INC-014",
                "task_type": "task3",
                "action": "FAILOVER",
            },
        )

        self.assertEqual(step_response.status_code, 200)
        step_body = step_response.json()
        self.assertTrue(step_body["done"])
        self.assertEqual(step_body["reward"]["value"], 1.0)
        self.assertTrue(step_body["info"]["correct"])
        self.assertEqual(step_body["info"]["ground_truth"], "FAILOVER")

        state_response = self.client.get(f"/state?session_id={session_id}")
        self.assertEqual(state_response.status_code, 200)
        state_body = state_response.json()
        self.assertTrue(state_body["done"])
        self.assertEqual(state_body["status"], "completed")
        self.assertEqual(state_body["last_reward"], 1.0)

    def test_step_rejects_action_for_wrong_task_type(self) -> None:
        reset_response = self.client.post(
            "/reset",
            json={"task_type": "task3", "ticket_id": "INC-014"},
        )
        session_id = reset_response.json()["info"]["session_id"]

        step_response = self.client.post(
            f"/step?session_id={session_id}",
            json={
                "incident_id": "INC-014",
                "task_type": "task2",
                "root_cause": "NETWORK",
            },
        )

        self.assertEqual(step_response.status_code, 400)
        self.assertIn("does not match", step_response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
