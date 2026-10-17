"""Restricted Supabase RPC transport, with purpose-specific API tokens."""
import json
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError


class InboxTransportError(RuntimeError):
    """Safe diagnostic metadata; never includes upstream body or credentials."""

    def __init__(self, category, status=None):
        self.category = category
        self.status = status
        super().__init__(f'inbox_{category} status={status or "none"}')


class SupabaseInbox:
    def __init__(self, url, publishable_key, receiver_token, visibility_seconds=60):
        if urlparse(url).scheme != 'https' or not publishable_key or not receiver_token:
            raise ValueError('HTTPS Supabase URL and receiver credentials are required')
        self.url = url.rstrip('/')
        self.key = publishable_key
        self.token = receiver_token
        self.visibility_seconds = visibility_seconds

    def rpc(self, name, body):
        request = Request(
            self.url + '/rest/v1/rpc/' + name, data=json.dumps(body).encode(),
            headers={'apikey': self.key, 'x-video-inbox-key': self.token,
                     'Content-Type': 'application/json'}, method='POST',
        )
        try:
            with urlopen(request, timeout=15) as response:
                return json.load(response)
        except HTTPError as exc:
            category = 'credentials' if exc.code in (401, 403) else 'rate_limit' if exc.code == 429 else 'upstream'
            exc.close()
            raise InboxTransportError(category, exc.code) from None
        except (URLError, TimeoutError):
            raise InboxTransportError('network') from None
        except (ValueError, UnicodeError):
            raise InboxTransportError('invalid_response') from None

    def read(self):
        # One at a time: visibility is for local insertion, never video processing.
        return self.rpc('video_inbox_read', {'visibility_seconds': self.visibility_seconds})

    def delete(self, message_id):
        self.rpc('video_inbox_delete', {'message_id': message_id})
