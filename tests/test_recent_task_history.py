import unittest
from types import SimpleNamespace

from datetime import datetime, timedelta

from src.apps.ui.streamlit_app import (
    _build_recent_task_entry,
    _prune_recent_history,
    RECENT_TASK_HISTORY_TTL_DAYS,
)


class RecentTaskHistoryTests(unittest.TestCase):
    def test_build_recent_entry_prefers_title_and_notion_url(self):
        task = SimpleNamespace(
            id="123",
            title="My Task",
            url="http://example.com",
            notion_url="https://notion.so/abc",
            notion_page_id=None,
        )

        entry = _build_recent_task_entry(task, "https://notion.so")

        self.assertEqual(entry["id"], "123")
        self.assertEqual(entry["title"], "My Task")
        self.assertEqual(entry["url"], "http://example.com")
        self.assertEqual(entry["notion_url"], "https://notion.so/abc")
        self.assertIsInstance(entry["viewed_at"], str)

    def test_build_recent_entry_uses_base_url_and_page_id(self):
        task = SimpleNamespace(
            id=5,
            title=None,
            url="http://example.com",
            notion_url=None,
            notion_page_id="abcd-1234",
        )

        entry = _build_recent_task_entry(task, "https://notion.so")

        self.assertEqual(entry["id"], "5")
        self.assertEqual(entry["title"], "http://example.com")
        self.assertEqual(entry["notion_url"], "https://notion.so/abcd1234")

    def test_prune_recent_history_keeps_recent_entries(self):
        now = datetime.utcnow()
        recent = (now - timedelta(days=1)).isoformat()
        stale = (now - timedelta(days=RECENT_TASK_HISTORY_TTL_DAYS + 1)).isoformat()
        history = [
            {"id": "1", "viewed_at": recent},
            {"id": "2", "viewed_at": stale},
            {"id": "3", "viewed_at": recent},
        ]

        pruned = _prune_recent_history(history)

        self.assertEqual([item["id"] for item in pruned], ["1", "3"])


if __name__ == "__main__":
    unittest.main()
