"""The bridge only trusts an explicit durable result from the local API."""
import unittest
from unittest.mock import Mock

from whisper_summary.infrastructure.task_queue.video_inbox_api import InboxApiError, VideoInboxApi
from whisper_summary.services.tasks.video_inbox import receive_message


class VideoInboxApiTransportTests(unittest.TestCase):
    def test_delivers_with_existing_worker_token(self):
        session = Mock()
        session.post.return_value.status_code = 200
        session.post.return_value.json.return_value = {'outcome': 'accepted'}
        api = VideoInboxApi('http://localhost:8080/', 'worker-secret', session=session)
        envelope = {'msg_id': 12, 'message': {'version': 1}}
        self.assertEqual(api.deliver(envelope), 'accepted')
        session.post.assert_called_once_with(
            'http://localhost:8080/video-inbox/messages', json=envelope,
            headers={'X-Worker-Token': 'worker-secret'}, timeout=15, allow_redirects=False,
        )

    def test_api_failure_or_unconfirmed_response_preserves_cloud_message(self):
        for status, outcome in [(503, None), (200, 'unknown')]:
            with self.subTest(status=status, outcome=outcome):
                session = Mock()
                session.post.return_value.status_code = status
                session.post.return_value.json.return_value = {'outcome': outcome}
                api = VideoInboxApi('http://localhost:8080', 'worker-secret', session=session)
                queue = Mock()
                with self.assertRaises(InboxApiError):
                    receive_message(api, queue, {'msg_id': 12, 'message': {}})
                queue.delete.assert_not_called()
