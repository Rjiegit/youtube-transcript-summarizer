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
        self.db.add_task("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        tasks = self.db.get_pending_tasks()
        self.assertEqual(len(tasks), 1)
        t = tasks[0]
        self.assertEqual(t.status, "Pending")
        self.assertTrue(t.created_at is not None)

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


if __name__ == "__main__":
    unittest.main()

