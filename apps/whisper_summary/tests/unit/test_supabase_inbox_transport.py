import io
import json
import unittest
from unittest.mock import patch

from whisper_summary.infrastructure.task_queue.supabase_inbox import SupabaseInbox


class SupabaseInboxTransportTests(unittest.TestCase):
    def test_read_uses_visibility_and_scoped_rpc(self):
        queue = SupabaseInbox('https://example.supabase.co', 'publishable', 'receiver')
        with patch('whisper_summary.infrastructure.task_queue.supabase_inbox.urlopen') as open_url:
            open_url.return_value.__enter__.return_value = io.BytesIO(b'[]')
            self.assertEqual(queue.read(), [])
            request = open_url.call_args.args[0]
            self.assertTrue(request.full_url.endswith('/rest/v1/rpc/video_inbox_read'))
            self.assertEqual(json.loads(request.data), {'visibility_seconds': 60})
            self.assertEqual(request.get_header('X-video-inbox-key'), 'receiver')
            self.assertIsNone(request.get_header('Authorization'))
            self.assertEqual(open_url.call_args.kwargs['timeout'], 15)

    def test_requires_https_and_credentials(self):
        with self.assertRaises(ValueError):
            SupabaseInbox('http://example.test', '', '')

    def test_http_error_is_classified_without_leaking_body(self):
        from urllib.error import HTTPError
        from whisper_summary.infrastructure.task_queue.supabase_inbox import InboxTransportError
        queue = SupabaseInbox('https://example.supabase.co', 'publishable', 'receiver')
        for status, category in [(401, 'credentials'), (403, 'credentials'), (429, 'rate_limit'), (503, 'upstream')]:
            with self.subTest(status=status), patch(
                'whisper_summary.infrastructure.task_queue.supabase_inbox.urlopen',
                side_effect=HTTPError('https://example.test', status, 'sensitive-token', {}, None),
            ):
                with self.assertRaises(InboxTransportError) as raised:
                    queue.read()
                self.assertEqual(raised.exception.category, category)
                self.assertEqual(raised.exception.status, status)
                self.assertNotIn('sensitive-token', str(raised.exception))

    def test_network_error_is_classified(self):
        from urllib.error import URLError
        from whisper_summary.infrastructure.task_queue.supabase_inbox import InboxTransportError
        queue = SupabaseInbox('https://example.supabase.co', 'publishable', 'receiver')
        with patch('whisper_summary.infrastructure.task_queue.supabase_inbox.urlopen', side_effect=URLError('private')):
            with self.assertRaises(InboxTransportError) as raised:
                queue.read()
            self.assertEqual(raised.exception.category, 'network')
