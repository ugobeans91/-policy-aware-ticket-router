import unittest

from fastapi.testclient import TestClient

from ticket_router.main import app


class HealthTest(unittest.TestCase):
    def test_health(self):
        with TestClient(app) as client:
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
