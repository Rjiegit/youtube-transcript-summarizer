import unittest
from unittest.mock import MagicMock

from whisper_summary.apps.api.dependencies import schedule_job


class TestAPIDedicatedWorkerBoundary(unittest.TestCase):
    def test_api_scheduler_never_starts_in_process_work(self) -> None:
        result = schedule_job(db_type="sqlite", db=MagicMock(), worker_id="requested")

        self.assertFalse(result.accepted)
        self.assertIsNone(result.worker_id)
        self.assertIn("dedicated processing worker", result.message)
