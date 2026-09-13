import os
import tempfile
import unittest

from src.infrastructure.persistence.sqlite.client import SQLiteDB
from src.infrastructure.persistence.sqlite.rss_subscription_repository import (
    SQLiteRSSSubscriptionRepository,
)
from src.services.rss.subscription_service import (
    create_rss_subscription,
    normalize_rss_subscription_input,
)


class TestRSSSubscriptionService(unittest.TestCase):
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

    def test_normalize_rss_subscription_input_accepts_feed_url(self) -> None:
        channel_id, feed_url = normalize_rss_subscription_input(
            "https://www.youtube.com/feeds/videos.xml?channel_id=UC1234567890123456789012"
        )
        self.assertEqual(channel_id, "UC1234567890123456789012")
        self.assertEqual(
            feed_url,
            "https://www.youtube.com/feeds/videos.xml?channel_id=UC1234567890123456789012",
        )

    def test_create_rss_subscription_persists_record(self) -> None:
        result = create_rss_subscription(
            self.repo,
            channel_id="UC1234567890123456789012",
            title="Demo Channel",
        )
        self.assertTrue(result.created)
        self.assertEqual(result.channel_id, "UC1234567890123456789012")
        self.assertEqual(result.message, "RSS subscription created.")

    def test_create_rss_subscription_rejects_duplicates(self) -> None:
        create_rss_subscription(
            self.repo,
            channel_id="UC1234567890123456789012",
        )
        with self.assertRaises(ValueError):
            create_rss_subscription(
                self.repo,
                channel_id="UC1234567890123456789012",
            )

    def test_create_rss_subscription_falls_back_title_to_channel_id(self) -> None:
        result = create_rss_subscription(
            self.repo,
            channel_id="UC9999999999999999999999",
            title="",
        )

        self.assertEqual(result.title, "UC9999999999999999999999")
        stored = self.repo.get_subscription(result.subscription_id or "")
        self.assertIsNotNone(stored)
        assert stored is not None
        self.assertEqual(stored.title, "UC9999999999999999999999")
