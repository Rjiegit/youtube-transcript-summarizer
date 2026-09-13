import threading
import unittest
from unittest.mock import MagicMock, patch

from src.apps.workers.processing_worker import run_forever


class TestDedicatedProcessingWorker(unittest.TestCase):
    @patch("src.apps.workers.processing_worker.create_database")
    def test_poll_loop_reuses_database_and_stops_cleanly(self, create_database) -> None:
        db = MagicMock()
        create_database.return_value = db
        stop_event = threading.Event()
        processor = MagicMock(side_effect=lambda **_: stop_event.set())

        run_forever(stop_event=stop_event, processor=processor, poll_interval_seconds=0.1)

        create_database.assert_called_once_with("sqlite")
        processor.assert_called_once_with(db=db, worker_id="processing-worker")

    @patch("src.apps.workers.processing_worker.create_database")
    def test_poll_loop_survives_failed_cycle(self, create_database) -> None:
        stop_event = threading.Event()
        calls = 0

        def processor(**_):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise RuntimeError("temporary failure")
            stop_event.set()

        run_forever(stop_event=stop_event, processor=processor, poll_interval_seconds=0.1)
        self.assertEqual(calls, 2)
