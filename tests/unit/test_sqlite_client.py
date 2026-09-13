import os
import sqlite3
import tempfile
import unittest

from src.infrastructure.persistence.sqlite.client import SQLiteDB


class TestSQLiteClient(unittest.TestCase):
    def setUp(self):
        # Use a temporary file for the SQLite DB
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        self.db = SQLiteDB(db_path=self.tmp.name)

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except FileNotFoundError:
            pass

    def test_add_and_get_pending_tasks(self):
        created = self.db.add_task("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        self.assertIsNotNone(created.id)
        self.assertEqual(created.status, "Pending")
        tasks = self.db.get_pending_tasks()
        self.assertEqual(len(tasks), 1)
        t = tasks[0]
        self.assertEqual(t.status, "Pending")
        self.assertTrue(t.created_at is not None)
        self.assertEqual(t.retry_of_task_id, None)
        self.assertEqual(t.retry_reason, "")
        self.assertIsNone(t.notion_page_id)

    def test_update_task_status_and_get_by_id(self):
        self.db.add_task("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        tasks = self.db.get_pending_tasks()
        t = tasks[0]

        self.db.update_task_status(
            t.id,
            status="Completed",
            title="Title A",
            summary="Summary...",
            error_message=None,
            processing_duration=1.23,
            notion_page_id="page-123",
        )

        got = self.db.get_task_by_id(t.id)
        self.assertEqual(got.status, "Completed")
        self.assertEqual(got.title, "Title A")
        self.assertAlmostEqual(got.processing_duration, 1.23, places=2)
        self.assertEqual(got.retry_of_task_id, None)
        self.assertEqual(got.retry_reason, "")
        self.assertEqual(got.notion_page_id, "page-123")

    def test_create_retry_task(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.db.add_task(url)
        original = self.db.get_pending_tasks()[0]

        # Mark the original task as failed with an error message.
        self.db.update_task_status(
            original.id,
            status="Failed",
            error_message="Network issue",
        )
        failed_task = self.db.get_task_by_id(original.id)

        retry_task = self.db.create_retry_task(failed_task)

        self.assertEqual(retry_task.status, "Pending")
        self.assertEqual(retry_task.url, url)
        self.assertEqual(retry_task.retry_of_task_id, str(original.id))
        self.assertEqual(retry_task.retry_reason, "Network issue")

        # Ensure the retry task is persisted in storage and retrievable.
        persisted = self.db.get_task_by_id(retry_task.id)
        self.assertEqual(persisted.retry_of_task_id, str(original.id))

    def test_acquire_next_task_marks_processing(self):
        self.db.add_task("https://youtu.be/example1")
        claimed = self.db.acquire_next_task(worker_id="worker-1")
        self.assertIsNotNone(claimed)
        self.assertEqual(claimed.status, "Processing")
        self.assertEqual(claimed.worker_id, "worker-1")
        self.assertIsNotNone(claimed.locked_at)

        # No more pending tasks remain.
        self.assertIsNone(self.db.acquire_next_task(worker_id="worker-1"))

    def test_acquire_next_task_reclaims_stale_processing_task(self):
        created = self.db.add_task("https://youtu.be/example2")
        first_claim = self.db.acquire_next_task("worker-2", lock_timeout_seconds=5)
        self.assertIsNotNone(first_claim)
        self.assertEqual(first_claim.worker_id, "worker-2")

        # Rewind locked_at to simulate a stalled worker.
        conn = sqlite3.connect(self.tmp.name)
        try:
            conn.execute(
                "UPDATE tasks SET locked_at = datetime('now', '-600 seconds') WHERE id = ?",
                (created.id,),
            )
            conn.commit()
        finally:
            conn.close()

        reclaimed = self.db.acquire_next_task("worker-3", lock_timeout_seconds=10)
        self.assertIsNotNone(reclaimed)
        self.assertEqual(reclaimed.id, created.id)
        self.assertEqual(reclaimed.worker_id, "worker-3")

    def test_processing_lock_allows_single_worker(self):
        self.assertTrue(
            self.db.acquire_processing_lock("worker-a", lock_timeout_seconds=30)
        )
        self.assertFalse(
            self.db.acquire_processing_lock("worker-b", lock_timeout_seconds=30)
        )

        self.db.release_processing_lock("worker-a")

        self.assertTrue(
            self.db.acquire_processing_lock("worker-b", lock_timeout_seconds=30)
        )

    def test_read_processing_lock_returns_current_owner(self):
        acquired = self.db.acquire_processing_lock("worker-info", lock_timeout_seconds=30)
        self.assertTrue(acquired)

        lock_info = self.db.read_processing_lock()
        self.assertEqual(lock_info.worker_id, "worker-info")
        self.assertIsNotNone(lock_info.locked_at)

    def test_clear_processing_lock_removes_owner(self):
        self.assertTrue(
            self.db.acquire_processing_lock("worker-clear", lock_timeout_seconds=30)
        )

        self.db.clear_processing_lock()
        lock_info = self.db.read_processing_lock()
        self.assertIsNone(lock_info.worker_id)
        self.assertIsNone(lock_info.locked_at)


if __name__ == "__main__":
    unittest.main()
