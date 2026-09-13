import os
import tempfile
import unittest
from datetime import datetime

from src.infrastructure.persistence.sqlite.client import SQLiteDB
from src.infrastructure.persistence.sqlite.rss_subscription_repository import (
    SQLiteRSSSubscriptionRepository,
)


class TestRSSSubscriptionRepository(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        self.db = SQLiteDB(db_path=self.tmp.name)
        self.repo = SQLiteRSSSubscriptionRepository(db_path=self.tmp.name)

    def tearDown(self) -> None:
        try:
            os.unlink(self.tmp.name)
        except FileNotFoundError:
            pass

    def test_add_and_list_subscription(self) -> None:
        created = self.repo.add_subscription(
            channel_id="UC1234567890123456789012",
            feed_url="https://www.youtube.com/feeds/videos.xml?channel_id=UC1234567890123456789012",
            title="Demo",
            enabled=True,
        )

        items = self.repo.list_subscriptions()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, created.id)
        self.assertEqual(items[0].title, "Demo")
        self.assertTrue(items[0].enabled)

    def test_update_monitor_state(self) -> None:
        created = self.repo.add_subscription(
            channel_id="UC1234567890123456789012",
            feed_url="https://www.youtube.com/feeds/videos.xml?channel_id=UC1234567890123456789012",
        )
        published_at = datetime(2026, 3, 29, 12, 0, 0)
        checked_at = datetime(2026, 3, 29, 12, 10, 0)

        self.repo.update_monitor_state(
            created.id,
            last_processed_published_at=published_at,
            last_checked_at=checked_at,
            last_status="success",
            last_error="",
        )

        reloaded = self.repo.get_subscription(created.id)
        self.assertIsNotNone(reloaded)
        assert reloaded is not None
        self.assertEqual(reloaded.last_status, "success")
        self.assertEqual(reloaded.last_processed_published_at, published_at)
        self.assertEqual(reloaded.last_checked_at, checked_at)

    def test_set_enabled_and_delete_subscription(self) -> None:
        created = self.repo.add_subscription(
            channel_id="UC1234567890123456789012",
            feed_url="https://www.youtube.com/feeds/videos.xml?channel_id=UC1234567890123456789012",
        )

        self.repo.set_enabled(created.id, False)
        disabled = self.repo.get_subscription(created.id)
        self.assertIsNotNone(disabled)
        assert disabled is not None
        self.assertFalse(disabled.enabled)

        self.repo.delete_subscription(created.id)
        self.assertIsNone(self.repo.get_subscription(created.id))
