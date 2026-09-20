import unittest
from unittest.mock import MagicMock

from whisper_summary.infrastructure.task_queue.http_client import (
    HttpTaskQueue,
    TaskLeaseLostError,
)


class TestHttpTaskQueue(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock()
        self.queue = HttpTaskQueue(
            "http://localhost:8080",
            "secret",
            session=self.session,
        )

    def test_claim_and_complete_use_the_same_lease(self):
        claim_response = MagicMock(status_code=200)
        claim_response.json.return_value = {
            "task": {
                "id": "42",
                "url": "https://youtu.be/example",
                "status": "Processing",
                "title": "Example",
                "notion_page_id": None,
                "processing_engine": "legacy",
            },
            "lease_token": "lease-123",
            "lease_expires_at": "2026-09-20T12:15:00",
        }
        complete_response = MagicMock(status_code=204)
        self.session.post.side_effect = [claim_response, complete_response]

        task = self.queue.acquire_next_task("local:abc")
        updated = self.queue.update_task_status(
            task.id,
            "Completed",
            title="Done",
            summary="Summary",
            processing_duration=1.5,
            notion_page_id="page-1",
        )

        self.assertTrue(updated)
        self.assertEqual(task.lease_token, "lease-123")
        complete_call = self.session.post.call_args_list[1]
        self.assertEqual(
            complete_call.kwargs["json"]["lease_token"],
            "lease-123",
        )
        self.assertEqual(
            complete_call.kwargs["json"]["worker_id"],
            "local:abc",
        )

    def test_empty_queue_returns_none(self):
        response = MagicMock(status_code=204)
        self.session.post.return_value = response

        self.assertIsNone(self.queue.acquire_next_task("docker:abc"))

    def test_lease_conflict_raises_specific_error(self):
        response = MagicMock(status_code=409, text="lost")
        self.session.post.return_value = response
        self.queue._leases["42"] = ("local:abc", "lease-123")

        with self.assertRaises(TaskLeaseLostError):
            self.queue.refresh_task_lease("42", "local:abc", "lease-123")


if __name__ == "__main__":
    unittest.main()
