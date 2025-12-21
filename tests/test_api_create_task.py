import json
import os
import sys
import types
import unittest
from datetime import datetime, timedelta
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
    from src.apps.api.main import app
except ModuleNotFoundError:  # pragma: no cover - testing scaffold
    TestClient = None
    app = None
    HTTPException = RuntimeError  # type: ignore
    status = types.SimpleNamespace(HTTP_500_INTERNAL_SERVER_ERROR=500)  # type: ignore

from src.domain.interfaces.database import ProcessingLockInfo
from src.domain.tasks.models import Task
from src.services.pipeline.processing_runner import (
    PROCESSING_LOCK_TIMEOUT_SECONDS,
    ProcessingSummary,
)


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

        with patch("src.apps.api.main.DBFactory.get_db", return_value=mock_db) as mock_get_db:
            with patch(
                "src.apps.api.main.process_pending_tasks",
                side_effect=_fake_process_pending_tasks,
            ):
                with patch("src.apps.api.main.threading.Thread", side_effect=_thread_stub) as mock_thread:
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
        self.assertEqual(mock_get_db.call_count, 2)
        mock_get_db.assert_any_call("sqlite")
        mock_db.add_task.assert_called_once_with(self.normalized_url)
        mock_db.acquire_processing_lock.assert_called_once()
        mock_db.release_processing_lock.assert_called_once_with(worker_id_used)
        mock_thread.assert_called_once()

    def test_create_task_invalid_url(self) -> None:
        with patch("src.apps.api.main.DBFactory.get_db") as mock_get_db:
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
            with patch("src.apps.api.main.DBFactory.get_db") as mock_get_db:
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
            with patch("src.apps.api.main.DBFactory.get_db", return_value=mock_db) as mock_get_db:
                with patch(
                    "src.apps.api.main.process_pending_tasks",
                    side_effect=_fake_process_pending_tasks,
                ):
                    with patch(
                        "src.apps.api.main.threading.Thread",
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
        self.assertEqual(mock_get_db.call_count, 2)
        mock_get_db.assert_any_call("notion")
        mock_db.add_task.assert_called_once_with(self.normalized_url)
        mock_db.release_processing_lock.assert_called_once_with(worker_id_used)
        mock_thread.assert_called_once()

    def test_create_task_db_factory_error(self) -> None:
        with patch(
            "src.apps.api.main.DBFactory.get_db",
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

        with patch("src.apps.api.main.DBFactory.get_db", return_value=mock_db):
            response = self.client.post("/tasks", json={"url": self.valid_url})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "boom")

    def test_create_task_returns_message_when_processing_locked(self) -> None:
        mock_db = MagicMock()
        mock_db.add_task.return_value = Task(id="1", url=self.normalized_url, status="Pending")
        mock_db.acquire_processing_lock.return_value = False

        with patch("src.apps.api.main.DBFactory.get_db", return_value=mock_db):
            with patch("src.apps.api.main.threading.Thread") as mock_thread:
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

        with patch("src.apps.api.main.DBFactory.get_db", return_value=mock_db):
            with patch(
                "src.apps.api.main._schedule_processing_job",
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

        with patch("src.apps.api.main.DBFactory.get_db", return_value=mock_db) as mock_get_db:
            with patch(
                "src.apps.api.main.process_pending_tasks", return_value=mock_summary
            ) as mock_process:
                with patch("src.apps.api.main.threading.Thread", side_effect=_thread_stub):
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

        with patch("src.apps.api.main.DBFactory.get_db", return_value=mock_db):
            response = self.client.post(
                "/processing-jobs",
                json={"db_type": "sqlite"},
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"], "Processing already running.")
        mock_db.release_processing_lock.assert_not_called()


@unittest.skipIf(TestClient is None, "fastapi is not installed")
class TestRetryTaskEndpoint(unittest.TestCase):
    """Tests for the POST /tasks/{task_id}/retry endpoint."""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_retry_task_success_for_failed(self) -> None:
        source_task = Task(
            id="10",
            url="https://youtu.be/example",
            status="Failed",
            error_message="boom",
        )
        retry_task = Task(
            id="11",
            url=source_task.url,
            status="Pending",
            retry_of_task_id="10",
            retry_reason="manual",
        )
        mock_db = MagicMock()
        mock_db.get_task_by_id.return_value = source_task
        mock_db.create_retry_task.return_value = retry_task

        with patch("src.apps.api.main.DBFactory.get_db", return_value=mock_db):
            response = self.client.post(
                "/tasks/10/retry",
                json={"db_type": "sqlite", "retry_reason": "manual"},
            )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["task_id"], "11")
        self.assertEqual(payload["source_task_id"], "10")
        self.assertEqual(payload["status"], "Pending")
        self.assertEqual(payload["db_type"], "sqlite")
        self.assertIn("Retry task created", payload["message"])
        mock_db.get_task_by_id.assert_called_once_with("10")
        mock_db.create_retry_task.assert_called_once_with(source_task, "manual")
        mock_db.update_task_status.assert_called_once_with("10", "Failed Retry Created")

    def test_retry_task_rejects_non_failed(self) -> None:
        source_task = Task(id="20", url="https://youtu.be/example", status="Completed")
        mock_db = MagicMock()
        mock_db.get_task_by_id.return_value = source_task

        with patch("src.apps.api.main.DBFactory.get_db", return_value=mock_db):
            response = self.client.post("/tasks/20/retry", json={"db_type": "sqlite"})

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["detail"],
            "Task status must be Failed to retry.",
        )
        mock_db.create_retry_task.assert_not_called()
        mock_db.update_task_status.assert_not_called()

    def test_retry_task_not_found(self) -> None:
        mock_db = MagicMock()
        mock_db.get_task_by_id.return_value = None

        with patch("src.apps.api.main.DBFactory.get_db", return_value=mock_db):
            response = self.client.post("/tasks/missing/retry", json={"db_type": "sqlite"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Task not found.")
        mock_db.create_retry_task.assert_not_called()
        mock_db.update_task_status.assert_not_called()

    def test_retry_task_requires_notion_env(self) -> None:
        with patch.dict(
            os.environ,
            {"NOTION_API_KEY": "", "NOTION_DATABASE_ID": ""},
            clear=False,
        ):
            with patch("src.apps.api.main.DBFactory.get_db") as mock_get_db:
                response = self.client.post(
                    "/tasks/10/retry",
                    json={"db_type": "notion"},
                )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing Notion configuration", response.json()["detail"])
        mock_get_db.assert_not_called()


@unittest.skipIf(TestClient is None, "fastapi is not installed")
class TestProcessingLockEndpoints(unittest.TestCase):
    """Tests for the GET/DELETE /processing-lock endpoints."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.admin_token = "lock-secret"

    def test_processing_lock_status_requires_token(self) -> None:
        with patch.dict(os.environ, {"PROCESSING_LOCK_ADMIN_TOKEN": self.admin_token}, clear=False):
            response = self.client.get("/processing-lock")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Missing maintainer token.")

    def test_processing_lock_status_returns_snapshot(self) -> None:
        locked_at = datetime.utcnow() - timedelta(seconds=PROCESSING_LOCK_TIMEOUT_SECONDS + 60)
        lock_info = ProcessingLockInfo(worker_id="api-worker-xyz", locked_at=locked_at)
        mock_db = MagicMock()
        mock_db.read_processing_lock.return_value = lock_info

        with patch.dict(os.environ, {"PROCESSING_LOCK_ADMIN_TOKEN": self.admin_token}, clear=False):
            with patch("src.apps.api.main.DBFactory.get_db", return_value=mock_db):
                response = self.client.get(
                    "/processing-lock",
                    headers={"X-Maintainer-Token": self.admin_token},
                )

        self.assertEqual(response.status_code, 200)
        snapshot = response.json()["snapshot"]
        self.assertEqual(snapshot["worker_id"], "api-worker-xyz")
        self.assertTrue(snapshot["stale"])

    def test_processing_lock_delete_dry_run(self) -> None:
        lock_info = ProcessingLockInfo(
            worker_id="api-worker-lock",
            locked_at=datetime.utcnow() - timedelta(seconds=30),
        )
        mock_db = MagicMock()
        mock_db.read_processing_lock.return_value = lock_info

        with patch.dict(os.environ, {"PROCESSING_LOCK_ADMIN_TOKEN": self.admin_token}, clear=False):
            with patch("src.apps.api.main.DBFactory.get_db", return_value=mock_db):
                response = self.client.request(
                    "DELETE",
                    "/processing-lock",
                    json={"dry_run": True},
                    headers={"X-Maintainer-Token": self.admin_token},
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["released"])
        self.assertEqual(payload["reason"], "dry_run")
        self.assertEqual(payload["before"], payload["after"])
        mock_db.release_processing_lock.assert_not_called()
        mock_db.clear_processing_lock.assert_not_called()

    def test_processing_lock_delete_with_expected_worker(self) -> None:
        before = ProcessingLockInfo(
            worker_id="api-worker-sanity",
            locked_at=datetime.utcnow() - timedelta(seconds=120),
        )
        after = ProcessingLockInfo(worker_id=None, locked_at=None)
        mock_db = MagicMock()
        mock_db.read_processing_lock.side_effect = [before, after]

        with patch.dict(os.environ, {"PROCESSING_LOCK_ADMIN_TOKEN": self.admin_token}, clear=False):
            with patch("src.apps.api.main.DBFactory.get_db", return_value=mock_db):
                response = self.client.request(
                    "DELETE",
                    "/processing-lock",
                    json={
                        "expected_worker_id": "api-worker-sanity",
                        "reason": "worker stuck after deploy",
                    },
                    headers={"X-Maintainer-Token": self.admin_token},
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["released"])
        self.assertEqual(payload["reason"], "worker stuck after deploy")
        self.assertEqual(payload["before"]["worker_id"], "api-worker-sanity")
        self.assertIsNone(payload["after"]["worker_id"])
        mock_db.release_processing_lock.assert_called_once_with("api-worker-sanity")
        mock_db.clear_processing_lock.assert_not_called()

    def test_processing_lock_force_threshold_conflict(self) -> None:
        lock_info = ProcessingLockInfo(
            worker_id="api-worker-force",
            locked_at=datetime.utcnow(),
        )
        mock_db = MagicMock()
        mock_db.read_processing_lock.return_value = lock_info

        with patch.dict(os.environ, {"PROCESSING_LOCK_ADMIN_TOKEN": self.admin_token}, clear=False):
            with patch("src.apps.api.main.DBFactory.get_db", return_value=mock_db):
                response = self.client.request(
                    "DELETE",
                    "/processing-lock",
                    json={"force": True, "force_threshold_seconds": 60},
                    headers={"X-Maintainer-Token": self.admin_token},
                )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()["detail"],
            "Processing lock has not aged enough for a forced release.",
        )
        mock_db.clear_processing_lock.assert_not_called()

    def test_processing_lock_force_successful_release(self) -> None:
        before = ProcessingLockInfo(
            worker_id="api-worker-forceable",
            locked_at=datetime.utcnow() - timedelta(seconds=3_600),
        )
        after = ProcessingLockInfo(worker_id=None, locked_at=None)
        mock_db = MagicMock()
        mock_db.read_processing_lock.side_effect = [before, after]

        with patch.dict(os.environ, {"PROCESSING_LOCK_ADMIN_TOKEN": self.admin_token}, clear=False):
            with patch("src.apps.api.main.DBFactory.get_db", return_value=mock_db):
                response = self.client.request(
                    "DELETE",
                    "/processing-lock",
                    json={
                        "force": True,
                        "force_threshold_seconds": 1200,
                        "reason": "cleanup",
                    },
                    headers={"X-Maintainer-Token": self.admin_token},
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["released"])
        self.assertEqual(payload["reason"], "cleanup")
        self.assertIsNone(payload["after"]["worker_id"])
        mock_db.clear_processing_lock.assert_called_once()
        mock_db.release_processing_lock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
