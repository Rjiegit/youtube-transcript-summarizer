import os
import tempfile
import unittest
from types import SimpleNamespace

from src.apps.ui.ui_rss import (
    add_rss_subscription,
    format_rss_poll_results,
    normalize_rss_subscription_input,
    trigger_rss_poll_once,
)
from src.infrastructure.persistence.sqlite.client import SQLiteDB
from src.infrastructure.persistence.sqlite.rss_subscription_repository import (
    SQLiteRSSSubscriptionRepository,
)


class TestUIRSSHelpers(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        SQLiteDB(db_path=self.tmp.name)
        self.repo = SQLiteRSSSubscriptionRepository(db_path=self.tmp.name)

    def tearDown(self) -> None:
        try:
            os.unlink(self.tmp.name)
        except FileNotFoundError:
            pass

    def test_normalize_rss_subscription_input_accepts_channel_id(self) -> None:
        channel_id, feed_url = normalize_rss_subscription_input("UC1234567890123456789012")
        self.assertEqual(channel_id, "UC1234567890123456789012")
        self.assertEqual(
            feed_url,
            "https://www.youtube.com/feeds/videos.xml?channel_id=UC1234567890123456789012",
        )

    def test_add_rss_subscription_rejects_duplicates(self) -> None:
        add_rss_subscription(self.repo, "UC1234567890123456789012", title="Demo")
        with self.assertRaises(ValueError):
            add_rss_subscription(self.repo, "UC1234567890123456789012", title="Demo")

    def test_trigger_rss_poll_once_uses_monitor_factory(self) -> None:
        captured = {}

        class FakeMonitor:
            def __init__(self, db, repository):
                captured["db_path"] = db.db_path
                captured["repo_type"] = type(repository).__name__

            def poll_once(self):
                return ["ok"]

        result = trigger_rss_poll_once(self.tmp.name, monitor_factory=FakeMonitor)

        self.assertEqual(result, ["ok"])
        self.assertEqual(captured["db_path"], self.tmp.name)
        self.assertEqual(captured["repo_type"], "SQLiteRSSSubscriptionRepository")

    def test_format_rss_poll_results(self) -> None:
        lines = format_rss_poll_results(
            [
                SimpleNamespace(
                    channel_id="UC1",
                    status="seeded",
                    seeded=True,
                    new_tasks=0,
                    duplicates=0,
                ),
                SimpleNamespace(
                    channel_id="UC2",
                    status="success",
                    seeded=False,
                    new_tasks=2,
                    duplicates=1,
                ),
                SimpleNamespace(
                    channel_id="UC3",
                    status="error",
                    seeded=False,
                    error="boom",
                ),
            ]
        )

        self.assertEqual(
            lines,
            [
                "UC1: seeded only, no historical videos queued",
                "UC2: new=2, duplicate=1",
                "UC3: error, boom",
            ],
        )
