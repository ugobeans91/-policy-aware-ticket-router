import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from ticket_router.main import app
from ticket_router.routing import POLICY


class RouteTest(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        self.enterContext(patch.dict(os.environ, {"ROUTER_DB_PATH": str(Path(directory) / "test.db")}))
        self.client = self.enterContext(TestClient(app))
        self.model = self.enterContext(patch("ticket_router.routing.request_model"))
        self.model.return_value = '{"outcome":"billing","policy_id":"BIL-01"}'

    def route(self, text="I was charged twice.", key="attempt-1"):
        return self.client.post(
            "/route", headers={"Idempotency-Key": key}, json={"ticket_id": "T1", "text": text}
        )

    def test_saved_decision_replayed_and_conflicting_request_rejected(self):
        response = self.route()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["outcome"], "billing")
        self.assertEqual(response.json()["policy_id"], "BIL-01")
        self.assertEqual(self.route().json(), response.json())
        self.assertEqual(self.route(text="My item arrived broken.").status_code, 409)
        self.model.assert_called_once()

    def test_invalid_decisions(self):
        for index, output in enumerate(("not json", '{"outcome":"billing","policy_id":"RET-01"}',
                                       '{"outcome":"billing","policy_id":"UNKNOWN"}')):
            with self.subTest(output=output):
                self.model.return_value = output
                response = self.route(key=f"invalid-{index}")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["outcome"], "human_review")
                self.assertIsNone(response.json()["policy_id"])
                self.assertEqual(response.json()["fallback_reason"], "invalid_model_response")

    def test_timeout_fallback_is_saved(self):
        self.model.side_effect = httpx.ReadTimeout("timed out")
        response = self.route()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["fallback_reason"], "model_timeout")
        self.assertEqual(self.route().json(), response.json())
        self.model.assert_called_once()

    def test_policy_review_keeps_model_attribution(self):
        self.model.return_value = '{"outcome":"human_review","policy_id":"REV-02"}'
        self.assertEqual(self.route(text="Help").json()["source"], "model")

    def test_blank_input_rejected(self):
        self.assertEqual(self.route(text=" ").status_code, 422)
        self.assertEqual(self.route(key=" ").status_code, 422)
        self.model.assert_not_called()

    def test_packaged_policy_matches_documentation(self):
        policy_doc = Path(__file__).resolve().parents[1] / "docs" / "routing-rules.md"
        self.assertEqual(POLICY.strip(), policy_doc.read_text().split("\nEach fixture")[0].strip())
