from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timedelta

from src.infrastructure.persistence.sqlite.client import SQLiteDB


class TestRecentHistorySQLite(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_tasks.db")
        self.db = SQLiteDB(db_path=self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_record_recent_task_view_dedup_and_order(self) -> None:
        first_time = datetime(2024, 1, 1, 12, 0, 0)
        second_time = first_time + timedelta(minutes=5)
        third_time = second_time + timedelta(minutes=5)

        self.db.record_recent_task_view("1", first_time)
        self.db.record_recent_task_view("2", second_time)

        history = self.db.list_recent_task_history()
        self.assertEqual([item["id"] for item in history], ["2", "1"])

        self.db.record_recent_task_view("1", third_time)

        history = self.db.list_recent_task_history()
        self.assertEqual([item["id"] for item in history], ["1", "2"])
        self.assertEqual(len(history), 2)

    def test_prune_recent_task_history(self) -> None:
        old_time = datetime(2024, 1, 1, 12, 0, 0)
        recent_time = datetime(2024, 1, 15, 12, 0, 0)

        self.db.record_recent_task_view("old", old_time)
        self.db.record_recent_task_view("recent", recent_time)

        cutoff = datetime(2024, 1, 10, 0, 0, 0)
        self.db.prune_recent_task_history(cutoff)

        history = self.db.list_recent_task_history()
        self.assertEqual([item["id"] for item in history], ["recent"])


if __name__ == "__main__":
    unittest.main()
