"""HTTP adapter for the local API's durable inbox endpoint."""
import requests


class InboxApiError(RuntimeError):
    """Safe metadata for bridge retries; excludes response bodies and credentials."""

    def __init__(self, category, status=None):
        self.category = category
        self.status = status
        super().__init__(f'inbox_api_{category} status={status or "none"}')


class VideoInboxApi:
    def __init__(self, base_url, worker_token, *, session=None):
        if not base_url or not worker_token:
            raise ValueError('TASK_API_BASE_URL and PROCESSING_WORKER_TOKEN are required')
        self.url = base_url.rstrip('/') + '/video-inbox/messages'
        self.worker_token = worker_token
        self.session = session or requests.Session()

    def deliver(self, envelope):
        try:
            response = self.session.post(
                self.url, json=envelope, headers={'X-Worker-Token': self.worker_token},
                timeout=15, allow_redirects=False,
            )
        except requests.RequestException:
            raise InboxApiError('network') from None
        if response.status_code in (401, 403):
            raise InboxApiError('credentials', response.status_code)
        if response.status_code == 429:
            raise InboxApiError('rate_limit', response.status_code)
        if response.status_code != 200:
            raise InboxApiError('local_api', response.status_code)
        try:
            outcome = response.json()['outcome']
        except (ValueError, KeyError, TypeError):
            raise InboxApiError('invalid_response') from None
        if outcome not in ('accepted', 'quarantined'):
            raise InboxApiError('invalid_response')
        return outcome
