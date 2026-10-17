import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock
from uuid import uuid4

from whisper_summary.infrastructure.persistence.sqlite.client import SQLiteDB
from whisper_summary.services.tasks.video_inbox import persist_message, receive_message


class VideoInboxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = SQLiteDB(str(Path(self.temp.name) / 'tasks.db'))
        self.message = {'submission_id': str(uuid4()), 'url': 'https://youtu.be/dQw4w9WgXcQ', 'version': 1}

    def test_redelivery_after_delete_failure(self):
        queue = Mock()
        api = Mock()
        api.deliver.side_effect = lambda envelope: persist_message(self.db, envelope)
        queue.delete.side_effect = RuntimeError('offline')
        with self.assertRaises(RuntimeError):
            receive_message(api, queue, {'msg_id': 1, 'message': self.message})
        queue.delete.side_effect = None
        receive_message(api, queue, {'msg_id': 1, 'message': self.message})
        self.assertEqual(len(self.db.get_all_tasks()), 1)

    def test_concurrent_ids_and_normalized_url(self):
        def accept(_):
            return self.db.accept_video_submission(self.message, cache_ttl_seconds=3600)
        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(accept, range(8)))
        self.assertEqual(len(set(ids)), 1)
        other = dict(self.message, submission_id=str(uuid4()), url='https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        self.assertEqual(self.db.accept_video_submission(other), ids[0])
        self.assertEqual(len(self.db.get_all_tasks()), 1)

    def test_write_failure_does_not_delete(self):
        queue = Mock()
        with self.assertRaises(RuntimeError):
            receive_message(Mock(deliver=Mock(side_effect=RuntimeError())), queue,
                            {'msg_id': 1, 'message': self.message})
        queue.delete.assert_not_called()

    def test_invalid_message_quarantined_before_delete(self):
        self.assertEqual(persist_message(self.db, {'msg_id': 2, 'message': {'version': 99}}), 'quarantined')
        self.assertEqual(len(self.db.get_all_tasks()), 0)

    def test_transaction_rolls_back(self):
        with self.db._get_connection() as conn:
            conn.execute("CREATE TRIGGER reject_receipt BEFORE INSERT ON video_inbox_receipts "
                         "BEGIN SELECT RAISE(ABORT, 'injected'); END")
        with self.assertRaises(Exception):
            self.db.accept_video_submission(self.message)
        self.assertEqual(self.db.get_all_tasks(), [])

    def test_completed_cache_policy(self):
        task_id = self.db.accept_video_submission(self.message)
        self.db.update_task_status(task_id, 'Completed')
        other = dict(self.message, submission_id=str(uuid4()))
        self.assertEqual(self.db.accept_video_submission(other), task_id)
        third = dict(self.message, submission_id=str(uuid4()))
        self.assertNotEqual(self.db.accept_video_submission(third, cache_ttl_seconds=0), task_id)

    def test_conflicting_id_is_quarantined(self):
        self.db.accept_video_submission(self.message)
        other = dict(self.message, url='https://youtu.be/abcdefghijk')
        self.assertEqual(persist_message(self.db, {'msg_id': 3, 'message': other}), 'quarantined')
        self.assertEqual(len(self.db.get_all_tasks()), 1)

    def test_poll_immediate_drain_idle_and_backoff(self):
        from whisper_summary.apps.workers.video_inbox_bridge import run_forever
        queue = Mock()
        queue.read.side_effect = [[{'msg_id': 1, 'message': self.message}], [], RuntimeError(), []]
        stop = Mock()
        stop.is_set.return_value = False
        delays = []

        def wait(delay):
            delays.append(delay)
            if len(delays) == 3:
                stop.is_set.return_value = True
        stop.wait.side_effect = wait
        api = Mock()
        api.deliver.side_effect = lambda envelope: persist_message(self.db, envelope)
        run_forever(api, queue, stop_event=stop)
        self.assertEqual(delays, [300, 5, 300])
        self.assertEqual(len(self.db.get_all_tasks()), 1)

    def test_existing_api_policy_and_bridge_share_atomic_creation(self):
        from whisper_summary.services.tasks.task_creation import create_task_record

        def create(index):
            if index % 2:
                return self.db.accept_video_submission(dict(self.message, submission_id=str(uuid4())))
            return str(create_task_record(db=self.db, url='https://www.youtube.com/watch?v=dQw4w9WgXcQ').task.id)
        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(create, range(12)))
        self.assertEqual(len(set(ids)), 1)
        self.assertEqual(len(self.db.get_all_tasks()), 1)

    def test_poll_reports_safe_diagnostics_for_credentials_and_api_errors(self):
        from whisper_summary.apps.workers.video_inbox_bridge import run_forever
        from whisper_summary.infrastructure.task_queue.supabase_inbox import InboxTransportError
        from whisper_summary.infrastructure.task_queue.video_inbox_api import InboxApiError
        for error, category in [(InboxTransportError('credentials', 403), 'credentials'),
                                (InboxApiError('local_api', 503), 'local_api')]:
            with self.subTest(category=category):
                queue = Mock()
                queue.read.side_effect = error
                stop = Mock()
                stop.is_set.return_value = False
                stop.wait.side_effect = lambda delay: setattr(stop.is_set, 'return_value', True)
                with self.assertLogs('whisper_summary.apps.workers.video_inbox_bridge', level='WARNING') as logs:
                    run_forever(Mock(), queue, stop_event=stop)
                self.assertIn('category=' + category, logs.output[0])
                self.assertEqual(queue.read.call_count, 1)
