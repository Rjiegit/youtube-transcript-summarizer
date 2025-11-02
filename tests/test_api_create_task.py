import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# Provide lightweight stubs for optional dependencies when running in minimal envs.
if "pytz" not in sys.modules:  # pragma: no cover - testing scaffold
    pytz_stub = types.ModuleType("pytz")

    def _fake_timezone(_name: str):
        class _FakeTZ:
            def localize(self, value):
                return value

        return _FakeTZ()

    pytz_stub.timezone = _fake_timezone
    sys.modules["pytz"] = pytz_stub

if "notion_client" not in sys.modules:  # pragma: no cover - testing scaffold
    notion_stub = types.ModuleType("notion_client")

    class _Client:  # minimal stub
        def __init__(self, *_, **__):
            pass

    notion_stub.Client = _Client
    sys.modules["notion_client"] = notion_stub

try:  # pragma: no cover - avoid hard dependency in minimal envs
    from fastapi import HTTPException, status
    from fastapi.testclient import TestClient
    from api.server import app
except ModuleNotFoundError:  # pragma: no cover - testing scaffold
    TestClient = None
    app = None
    HTTPException = RuntimeError  # type: ignore
    status = types.SimpleNamespace(HTTP_500_INTERNAL_SERVER_ERROR=500)  # type: ignore

from database.task import Task
from processing import ProcessingSummary, PROCESSING_LOCK_TIMEOUT_SECONDS


@unittest.skipIf(TestClient is None, "fastapi is not installed")
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
        mock_db.acquire_processing_lock.return_value = True

        def _fake_process_pending_tasks(*, db, worker_id, **_):
            return ProcessingSummary(
                worker_id=worker_id,
                processed_tasks=0,
                failed_tasks=0,
                acquired_lock=True,
            )

        def _thread_stub(target, args=(), kwargs=None, daemon=None):
            if kwargs is None:
                kwargs = {}

            class _ImmediateThread:
                def __init__(self):
                    self.daemon = daemon

                def start(self_inner):
                    target(*args, **kwargs)

            return _ImmediateThread()

        with patch("api.server.DBFactory.get_db", return_value=mock_db) as mock_get_db:
            with patch(
                "api.server.process_pending_tasks",
                side_effect=_fake_process_pending_tasks,
            ):
                with patch("api.server.threading.Thread", side_effect=_thread_stub) as mock_thread:
                    response = self.client.post("/tasks", json={"url": self.valid_url})

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["task_id"], "42")
        self.assertEqual(payload["status"], "Pending")
        self.assertEqual(payload["db_type"], "sqlite")
        self.assertTrue(payload["processing_started"])
        worker_id_used = mock_db.acquire_processing_lock.call_args[0][0]
        self.assertEqual(payload["processing_worker_id"], worker_id_used)
        self.assertIn("Processing worker scheduled", payload["message"])
        mock_get_db.assert_called_once_with("sqlite")
        mock_db.add_task.assert_called_once_with(self.normalized_url)
        mock_db.acquire_processing_lock.assert_called_once()
        mock_db.release_processing_lock.assert_called_once_with(worker_id_used)
        mock_thread.assert_called_once()

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
        mock_db.acquire_processing_lock.return_value = True

        def _fake_process_pending_tasks(*, db, worker_id, **_):
            return ProcessingSummary(
                worker_id=worker_id,
                processed_tasks=0,
                failed_tasks=0,
                acquired_lock=True,
            )

        def _thread_stub(target, args=(), kwargs=None, daemon=None):
            if kwargs is None:
                kwargs = {}

            class _ImmediateThread:
                def __init__(self):
                    self.daemon = daemon

                def start(self_inner):
                    target(*args, **kwargs)

            return _ImmediateThread()

        with patch.dict(
            os.environ,
            {"NOTION_API_KEY": "token", "NOTION_DATABASE_ID": "db"},
            clear=False,
        ):
            with patch("api.server.DBFactory.get_db", return_value=mock_db) as mock_get_db:
                with patch(
                    "api.server.process_pending_tasks",
                    side_effect=_fake_process_pending_tasks,
                ):
                    with patch(
                        "api.server.threading.Thread",
                        side_effect=_thread_stub,
                    ) as mock_thread:
                        response = self.client.post(
                            "/tasks",
                            json={"url": self.valid_url, "db_type": "notion"},
                        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["db_type"], "notion")
        self.assertEqual(payload["task_id"], "abc")
        self.assertTrue(payload["processing_started"])
        worker_id_used = mock_db.acquire_processing_lock.call_args[0][0]
        self.assertEqual(payload["processing_worker_id"], worker_id_used)
        self.assertIn("Processing worker scheduled", payload["message"])
        mock_get_db.assert_called_once_with("notion")
        mock_db.add_task.assert_called_once_with(self.normalized_url)
        mock_db.release_processing_lock.assert_called_once_with(worker_id_used)
        mock_thread.assert_called_once()

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

    def test_create_task_returns_message_when_processing_locked(self) -> None:
        mock_db = MagicMock()
        mock_db.add_task.return_value = Task(id="1", url=self.normalized_url, status="Pending")
        mock_db.acquire_processing_lock.return_value = False

        with patch("api.server.DBFactory.get_db", return_value=mock_db):
            with patch("api.server.threading.Thread") as mock_thread:
                response = self.client.post("/tasks", json={"url": self.valid_url})

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertFalse(payload["processing_started"])
        self.assertIsNone(payload["processing_worker_id"])
        self.assertIn("Processing already running", payload["message"])
        mock_thread.assert_not_called()

    def test_create_task_handles_scheduling_http_exception(self) -> None:
        mock_db = MagicMock()
        mock_db.add_task.return_value = Task(id="1", url=self.normalized_url, status="Pending")

        with patch("api.server.DBFactory.get_db", return_value=mock_db):
            with patch(
                "api.server._schedule_processing_job",
                side_effect=HTTPException(
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to schedule processing worker.",
                ),
            ):
                response = self.client.post("/tasks", json={"url": self.valid_url})

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertFalse(payload["processing_started"])
        self.assertIsNone(payload["processing_worker_id"])
        self.assertIn("Failed to schedule processing worker", payload["message"])

    def test_run_processing_endpoint_schedules_worker(self) -> None:
        mock_db = MagicMock()
        mock_db.acquire_processing_lock.return_value = True
        mock_summary = ProcessingSummary(
            worker_id="api-worker-123",
            processed_tasks=0,
            failed_tasks=0,
            acquired_lock=True,
        )

        def _thread_stub(target, args=(), kwargs=None, daemon=None):
            if kwargs is None:
                kwargs = {}

            class _ImmediateThread:
                def __init__(self):
                    self.daemon = daemon

                def start(self_inner):
                    target(*args, **kwargs)

            return _ImmediateThread()

        with patch("api.server.DBFactory.get_db", return_value=mock_db) as mock_get_db:
            with patch(
                "api.server.process_pending_tasks", return_value=mock_summary
            ) as mock_process:
                with patch("api.server.threading.Thread", side_effect=_thread_stub):
                    response = self.client.post(
                        "/processing-jobs",
                        json={"db_type": "sqlite", "worker_id": "api-worker-123"},
                    )

        self.assertEqual(response.status_code, 202)
        payload = response.json()
        self.assertTrue(payload["accepted"])
        self.assertEqual(payload["worker_id"], "api-worker-123")
        self.assertEqual(payload["db_type"], "sqlite")

        mock_get_db.assert_any_call("sqlite")
        mock_db.acquire_processing_lock.assert_called_once_with(
            "api-worker-123", PROCESSING_LOCK_TIMEOUT_SECONDS
        )
        mock_process.assert_called_once_with(
            db=mock_db,
            worker_id="api-worker-123",
        )
        mock_db.release_processing_lock.assert_called_once_with("api-worker-123")

    def test_run_processing_endpoint_conflict_when_locked(self) -> None:
        mock_db = MagicMock()
        mock_db.acquire_processing_lock.return_value = False

        with patch("api.server.DBFactory.get_db", return_value=mock_db):
            response = self.client.post(
                "/processing-jobs",
                json={"db_type": "sqlite"},
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"], "Processing already running.")
        mock_db.release_processing_lock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
