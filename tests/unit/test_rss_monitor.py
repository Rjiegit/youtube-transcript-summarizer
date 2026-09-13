import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from src.domain.rss.models import RSSChannelSubscription
from src.services.rss.channel_monitor import (
    RSSChannelMonitor,
    TaskEnqueueResult,
    YouTubeRSSFeedClient,
)


SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <yt:videoId>dQw4w9WgXcQ</yt:videoId>
    <title>Video One</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=dQw4w9WgXcQ"/>
    <published>2026-03-29T00:00:00+00:00</published>
    <updated>2026-03-29T00:05:00+00:00</updated>
  </entry>
  <entry>
    <yt:videoId>3JZ_D3ELwOQ</yt:videoId>
    <title>Video Two</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=3JZ_D3ELwOQ"/>
    <published>2026-03-29T01:00:00+00:00</published>
    <updated>2026-03-29T01:05:00+00:00</updated>
  </entry>
</feed>
"""


class TestYouTubeRSSFeedClient(unittest.TestCase):
    def test_parse_entries(self) -> None:
        client = YouTubeRSSFeedClient()

        entries = client.parse_entries(SAMPLE_FEED)

        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].video_id, "dQw4w9WgXcQ")
        self.assertEqual(entries[1].url, "https://www.youtube.com/watch?v=3JZ_D3ELwOQ")


class TestRSSChannelMonitor(unittest.TestCase):
    def test_first_poll_seeds_without_creating_tasks(self) -> None:
        db = MagicMock()
        repository = MagicMock()
        task_client = MagicMock()
        subscription = RSSChannelSubscription(
            id="1",
            channel_id="UC1234567890123456789012",
            feed_url="https://www.youtube.com/feeds/videos.xml?channel_id=UC1234567890123456789012",
        )
        repository.list_subscriptions.return_value = [subscription]
        feed_client = MagicMock()
        feed_client.fetch_entries.return_value = YouTubeRSSFeedClient().parse_entries(SAMPLE_FEED)
        monitor = RSSChannelMonitor(
            db=db,
            repository=repository,
            feed_client=feed_client,
            task_client=task_client,
        )

        results = monitor.poll_once()

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].seeded)
        task_client.enqueue_task.assert_not_called()
        repository.update_monitor_state.assert_called_once()

    def test_poll_creates_only_new_entries_via_api(self) -> None:
        db = MagicMock()
        repository = MagicMock()
        task_client = MagicMock()
        subscription = RSSChannelSubscription(
            id="1",
            channel_id="UC1234567890123456789012",
            feed_url="https://www.youtube.com/feeds/videos.xml?channel_id=UC1234567890123456789012",
            last_processed_published_at=datetime(2026, 3, 29, 0, 30, tzinfo=timezone.utc),
        )
        repository.list_subscriptions.return_value = [subscription]
        feed_client = MagicMock()
        feed_client.fetch_entries.return_value = YouTubeRSSFeedClient().parse_entries(SAMPLE_FEED)
        task_client.enqueue_task.return_value = TaskEnqueueResult(created=True)
        monitor = RSSChannelMonitor(
            db=db,
            repository=repository,
            feed_client=feed_client,
            task_client=task_client,
        )

        results = monitor.poll_once()

        self.assertEqual(results[0].new_tasks, 1)
        self.assertEqual(results[0].duplicates, 0)
        task_client.enqueue_task.assert_called_once_with(
            "https://www.youtube.com/watch?v=3JZ_D3ELwOQ",
            "UC1234567890123456789012",
        )

    def test_poll_counts_api_duplicates(self) -> None:
        db = MagicMock()
        repository = MagicMock()
        task_client = MagicMock()
        subscription = RSSChannelSubscription(
            id="1",
            channel_id="UC1234567890123456789012",
            feed_url="https://www.youtube.com/feeds/videos.xml?channel_id=UC1234567890123456789012",
            last_processed_published_at=datetime(2026, 3, 29, 0, 30, tzinfo=timezone.utc),
        )
        repository.list_subscriptions.return_value = [subscription]
        feed_client = MagicMock()
        feed_client.fetch_entries.return_value = YouTubeRSSFeedClient().parse_entries(SAMPLE_FEED)
        task_client.enqueue_task.return_value = TaskEnqueueResult(
            created=False,
            message="A completed task already exists for this URL.",
        )
        monitor = RSSChannelMonitor(
            db=db,
            repository=repository,
            feed_client=feed_client,
            task_client=task_client,
        )

        results = monitor.poll_once()

        self.assertEqual(results[0].new_tasks, 0)
        self.assertEqual(results[0].duplicates, 1)

    def test_poll_records_error_per_subscription(self) -> None:
        db = MagicMock()
        repository = MagicMock()
        subscription = RSSChannelSubscription(
            id="1",
            channel_id="UC1234567890123456789012",
            feed_url="https://www.youtube.com/feeds/videos.xml?channel_id=UC1234567890123456789012",
            last_processed_published_at=datetime(2026, 3, 29, 0, 0, tzinfo=timezone.utc),
        )
        repository.list_subscriptions.return_value = [subscription]
        feed_client = MagicMock()
        feed_client.fetch_entries.side_effect = RuntimeError("boom")
        monitor = RSSChannelMonitor(db=db, repository=repository, feed_client=feed_client)

        results = monitor.poll_once()

        self.assertEqual(results[0].status, "error")
        self.assertIn("boom", results[0].error)
        repository.update_monitor_state.assert_called_once()
