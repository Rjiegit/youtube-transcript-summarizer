import os
import tempfile
import unittest

from database.sqlite_client import SQLiteDB


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
        )

        got = self.db.get_task_by_id(t.id)
        self.assertEqual(got.status, "Completed")
        self.assertEqual(got.title, "Title A")
        self.assertAlmostEqual(got.processing_duration, 1.23, places=2)
        self.assertEqual(got.retry_of_task_id, None)
        self.assertEqual(got.retry_reason, "")

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


if __name__ == "__main__":
    unittest.main()
