import unittest
from datetime import timedelta
from unittest.mock import MagicMock

from src.core.time_utils import utc_now
from src.domain.tasks.models import Task
from src.services.tasks.task_creation import create_task_record


class TestTaskCreationService(unittest.TestCase):
    def setUp(self) -> None:
        self.url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_create_task_record_creates_new_manual_task(self) -> None:
        db = MagicMock()
        db.find_recent_task_by_url.return_value = None
        db.add_task.return_value = Task(id="1", url=self.url, status="Pending")

        result = create_task_record(db=db, url=self.url)

        self.assertTrue(result.created)
        self.assertEqual(result.outcome, "created")
        db.add_task.assert_called_once_with(
            self.url,
            source_type="manual",
            source_channel_id=None,
        )

    def test_create_task_record_uses_cache_ttl_for_manual(self) -> None:
        db = MagicMock()
        db.find_recent_task_by_url.return_value = Task(
            id="2",
            url=self.url,
            status="Completed",
            created_at=utc_now() - timedelta(seconds=60),
        )

        result = create_task_record(db=db, url=self.url, cache_ttl_seconds=3600)

        self.assertTrue(result.cached)
        self.assertEqual(result.outcome, "cached_completed")
        db.add_task.assert_not_called()

    def test_create_task_record_blocks_completed_task_for_rss(self) -> None:
        db = MagicMock()
        db.find_recent_task_by_url.return_value = Task(
            id="3",
            url=self.url,
            status="Completed",
            created_at=utc_now() - timedelta(days=3),
        )

        result = create_task_record(
            db=db,
            url=self.url,
            source_type="rss",
            source_channel_id="UC1234567890123456789012",
            completed_task_policy="block_existing",
        )

        self.assertEqual(result.outcome, "duplicate_completed")
        self.assertFalse(result.created)
        db.add_task.assert_not_called()
