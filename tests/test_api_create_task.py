import os
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from api.server import app
from database.task import Task


class TestCreateTaskEndpoint(unittest.TestCase):
    """Tests for the POST /tasks endpoint."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.valid_url = "https://youtu.be/dQw4w9WgXcQ"
        self.normalized_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_create_task_default_sqlite(self) -> None:
        mock_db = MagicMock()
        mock_db.add_task.return_value = Task(
            id="42",
            url=self.normalized_url,
            status="Pending",
        )

        with patch("api.server.DBFactory.get_db", return_value=mock_db) as mock_get_db:
            response = self.client.post("/tasks", json={"url": self.valid_url})

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["task_id"], "42")
        self.assertEqual(payload["status"], "Pending")
        self.assertEqual(payload["db_type"], "sqlite")
        mock_get_db.assert_called_once_with("sqlite")
        mock_db.add_task.assert_called_once_with(self.normalized_url)

    def test_create_task_invalid_url(self) -> None:
        with patch("api.server.DBFactory.get_db") as mock_get_db:
            response = self.client.post("/tasks", json={"url": "not-a-url"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid YouTube URL.")
        mock_get_db.assert_not_called()

    def test_create_task_requires_notion_env(self) -> None:
        with patch.dict(
            os.environ,
            {"NOTION_API_KEY": "", "NOTION_DATABASE_ID": ""},
            clear=False,
        ):
            with patch("api.server.DBFactory.get_db") as mock_get_db:
                response = self.client.post(
                    "/tasks",
                    json={"url": self.valid_url, "db_type": "notion"},
                )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing Notion configuration", response.json()["detail"])
        mock_get_db.assert_not_called()

    def test_create_task_notion_success_when_env_present(self) -> None:
        mock_db = MagicMock()
        mock_db.add_task.return_value = Task(
            id="abc",
            url=self.normalized_url,
            status="Pending",
        )

        with patch.dict(
            os.environ,
            {"NOTION_API_KEY": "token", "NOTION_DATABASE_ID": "db"},
            clear=False,
        ):
            with patch("api.server.DBFactory.get_db", return_value=mock_db) as mock_get_db:
                response = self.client.post(
                    "/tasks",
                    json={"url": self.valid_url, "db_type": "notion"},
                )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["db_type"], "notion")
        self.assertEqual(payload["task_id"], "abc")
        mock_get_db.assert_called_once_with("notion")
        mock_db.add_task.assert_called_once_with(self.normalized_url)

    def test_create_task_db_factory_error(self) -> None:
        with patch(
            "api.server.DBFactory.get_db",
            side_effect=ValueError("Unknown database type: foo"),
        ):
            response = self.client.post("/tasks", json={"url": self.valid_url})

        self.assertEqual(response.status_code, 422)
        self.assertIn("Unknown database type", response.json()["detail"])

    def test_create_task_unsupported_db_type(self) -> None:
        response = self.client.post(
            "/tasks",
            json={"url": self.valid_url, "db_type": "mongo"},
        )

        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertTrue(any("db_type" in err.get("loc", []) for err in detail))

    def test_create_task_database_failure(self) -> None:
        mock_db = MagicMock()
        mock_db.add_task.side_effect = RuntimeError("boom")

        with patch("api.server.DBFactory.get_db", return_value=mock_db):
            response = self.client.post("/tasks", json={"url": self.valid_url})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "boom")


if __name__ == "__main__":
    unittest.main()
