import os
import tempfile
import unittest
from datetime import timedelta
from types import SimpleNamespace
from unittest import mock

from src.core.time_utils import utc_now_naive
from src.apps.ui.streamlit_app import _build_recent_task_entry, _prune_recent_history
from src.apps.ui.ui_config import RECENT_TASK_HISTORY_TTL_DAYS
from src.infrastructure.persistence.sqlite.client import SQLiteDB


class RecentTaskHistoryTests(unittest.TestCase):
    def test_build_recent_entry_includes_id_and_viewed_at(self):
        task = SimpleNamespace(
            id="123",
            title="My Task",
            url="http://example.com",
            notion_url="https://notion.so/abc",
            notion_page_id=None,
        )

        entry = _build_recent_task_entry(task, "https://notion.so")

        self.assertEqual(entry["id"], "123")
        self.assertIsInstance(entry["viewed_at"], str)
        self.assertEqual(set(entry.keys()), {"id", "viewed_at"})

    def test_prune_recent_history_keeps_recent_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_tasks.db")
            db = SQLiteDB(db_path=db_path)
            now = utc_now_naive()
            db.record_recent_task_view(
                "recent",
                now - timedelta(days=1),
            )
            db.record_recent_task_view(
                "stale",
                now - timedelta(days=RECENT_TASK_HISTORY_TTL_DAYS + 1),
            )

            with mock.patch("src.apps.ui.ui_history._get_history_db", return_value=db):
                _prune_recent_history()

            history = db.list_recent_task_history()
            self.assertEqual([item["id"] for item in history], ["recent"])


if __name__ == "__main__":
    unittest.main()
