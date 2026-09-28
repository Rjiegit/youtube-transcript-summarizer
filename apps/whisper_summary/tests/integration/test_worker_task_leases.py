import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from whisper_summary.apps.api.main import app
from whisper_summary.domain.tasks.models import Task
from whisper_summary.infrastructure.persistence.sqlite.client import SQLiteDB


class TestWorkerTaskLeaseEndpoints(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.headers = {"X-Worker-Token": "worker-secret"}

    def test_claim_returns_task_and_lease(self) -> None:
        db = MagicMock()
        db.acquire_next_task.return_value = Task(
            id="42",
            url="https://youtu.be/example",
            status="Processing",
            title="Example",
            locked_at=datetime(2026, 9, 20, 12, 0, 0),
            worker_id="local:abc",
            lease_token="lease-123",
            processing_engine="legacy",
        )
        with patch.dict(
            os.environ,
            {"PROCESSING_WORKER_TOKEN": "worker-secret"},
            clear=False,
        ):
            with patch(
                "whisper_summary.apps.api.routers.processing.get_database",
                return_value=db,
            ):
                response = self.client.post(
                    "/worker-tasks/claim",
                    headers=self.headers,
                    json={"worker_id": "local:abc"},
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["task"]["id"], "42")
        self.assertEqual(payload["lease_token"], "lease-123")
        db.acquire_next_task.assert_called_once()

    def test_claim_returns_no_content_when_queue_is_empty(self) -> None:
        db = MagicMock()
        db.acquire_next_task.return_value = None
        with patch.dict(
            os.environ,
            {"PROCESSING_WORKER_TOKEN": "worker-secret"},
            clear=False,
        ):
            with patch(
                "whisper_summary.apps.api.routers.processing.get_database",
                return_value=db,
            ):
                response = self.client.post(
                    "/worker-tasks/claim",
                    headers=self.headers,
                    json={"worker_id": "docker:abc"},
                )

        self.assertEqual(response.status_code, 204)

    def test_heartbeat_rejects_a_lost_lease(self) -> None:
        db = MagicMock()
        db.refresh_task_lease.return_value = False
        with patch.dict(
            os.environ,
            {"PROCESSING_WORKER_TOKEN": "worker-secret"},
            clear=False,
        ):
            with patch(
                "whisper_summary.apps.api.routers.processing.get_database",
                return_value=db,
            ):
                response = self.client.post(
                    "/worker-tasks/42/heartbeat",
                    headers=self.headers,
                    json={
                        "worker_id": "local:abc",
                        "lease_token": "lease-123",
                    },
                )

        self.assertEqual(response.status_code, 409)

    def test_complete_updates_only_the_claimed_task(self) -> None:
        db = MagicMock()
        db.update_claimed_task.return_value = True
        with patch.dict(
            os.environ,
            {"PROCESSING_WORKER_TOKEN": "worker-secret"},
            clear=False,
        ):
            with patch(
                "whisper_summary.apps.api.routers.processing.get_database",
                return_value=db,
            ):
                response = self.client.post(
                    "/worker-tasks/42/complete",
                    headers=self.headers,
                    json={
                        "worker_id": "local:abc",
                        "lease_token": "lease-123",
                        "title": "Done",
                        "summary": "Summary",
                        "processing_duration": 2.5,
                    },
                )

        self.assertEqual(response.status_code, 204)
        db.update_claimed_task.assert_called_once_with(
            "42",
            "local:abc",
            "lease-123",
            status="Completed",
            title="Done",
            summary="Summary",
            processing_duration=2.5,
            notion_page_id=None,
            processing_engine=None,
        )

    def test_lists_all_active_processing_leases(self) -> None:
        db = MagicMock()
        db.list_processing_tasks.return_value = [
            Task(
                id="42",
                url="https://youtu.be/example",
                status="Processing",
                title="Example",
                locked_at=datetime.now(),
                worker_id="docker:abc",
                lease_token="lease-123",
            )
        ]
        with patch.dict(
            os.environ,
            {"PROCESSING_LOCK_ADMIN_TOKEN": "admin-secret"},
            clear=False,
        ):
            with patch(
                "whisper_summary.apps.api.routers.processing.get_database",
                return_value=db,
            ):
                response = self.client.get(
                    "/processing-leases",
                    headers={"X-Maintainer-Token": "admin-secret"},
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["leases"][0]["task_id"], "42")

    def test_two_api_workers_cannot_claim_the_same_task(self) -> None:
        temporary_db = tempfile.NamedTemporaryFile(delete=False)
        temporary_db.close()
        try:
            db = SQLiteDB(db_path=temporary_db.name)
            db.add_task("https://youtu.be/only-once")

            def claim(worker_id: str) -> int:
                response = self.client.post(
                    "/worker-tasks/claim",
                    headers=self.headers,
                    json={"worker_id": worker_id},
                )
                return response.status_code

            with patch.dict(
                os.environ,
                {"PROCESSING_WORKER_TOKEN": "worker-secret"},
                clear=False,
            ):
                with patch(
                    "whisper_summary.apps.api.routers.processing.get_database",
                    return_value=db,
                ):
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        statuses = list(
                            executor.map(claim, ("docker:abc", "local:abc"))
                        )

            self.assertEqual(sorted(statuses), [200, 204])
        finally:
            os.unlink(temporary_db.name)


if __name__ == "__main__":
    unittest.main()
