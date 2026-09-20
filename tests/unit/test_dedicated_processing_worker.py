import threading
import unittest
from unittest.mock import MagicMock, patch

from whisper_summary.apps.workers.processing_worker import (
    DEFAULT_POLL_INTERVAL_SECONDS,
    run_forever,
)


class TestDedicatedProcessingWorker(unittest.TestCase):
    def test_default_poll_interval_is_sixty_seconds(self) -> None:
        self.assertEqual(DEFAULT_POLL_INTERVAL_SECONDS, 60.0)

    @patch(
        "whisper_summary.apps.workers.processing_worker."
        "log_codex_cli_startup_status"
    )
    @patch("whisper_summary.apps.workers.processing_worker.create_task_queue")
    def test_poll_loop_reuses_database_and_stops_cleanly(
        self,
        create_task_queue,
        log_codex_status,
    ) -> None:
        db = MagicMock()
        create_task_queue.return_value = db
        stop_event = threading.Event()
        processor = MagicMock(side_effect=lambda **_: stop_event.set())

        run_forever(stop_event=stop_event, processor=processor, poll_interval_seconds=0.1)

        log_codex_status.assert_called_once_with()
        create_task_queue.assert_called_once_with()
        processor.assert_called_once_with(db=db, worker_id="processing-worker")

    @patch("whisper_summary.apps.workers.processing_worker.logger")
    @patch("whisper_summary.apps.workers.processing_worker.create_task_queue")
    def test_poll_loop_survives_failed_cycle(self, create_task_queue, logger) -> None:
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
        logger.exception.assert_called_once_with(
            "Processing worker processing-worker cycle failed (RuntimeError): RuntimeError('temporary failure')"
        )
