"""Inbox delivery: durable local commit must precede cloud acknowledgement."""
from uuid import UUID
from urllib.parse import urlparse

from whisper_summary.core.utils.url import normalize_youtube_url


def validate_message(message):
    if not isinstance(message, dict) or message.get('version') != 1:
        raise ValueError('unsupported_message')
    submission_id = str(UUID(message['submission_id']))
    url = message['url']
    parsed = urlparse(url)
    if parsed.scheme not in ('https', 'http') or parsed.netloc not in (
        'youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be',
    ):
        raise ValueError('invalid_source')
    normalized = normalize_youtube_url(url)
    if not normalized:
        raise ValueError('invalid_video')
    return submission_id, normalized


def persist_message(db, envelope, *, cache_ttl_seconds=3600):
    """Persist a task or quarantine record before the caller acknowledges the queue."""
    try:
        validate_message(envelope['message'])
    except (ValueError, KeyError, TypeError, AttributeError):
        db.quarantine_video_message(envelope)
        return 'quarantined'
    else:
        try:
            db.accept_video_submission(envelope['message'], cache_ttl_seconds=cache_ttl_seconds)
        except ValueError:
            db.quarantine_video_message(envelope)
            return 'quarantined'
    return 'accepted'


def receive_message(api, queue, envelope):
    """Acknowledge cloud delivery only after the local API confirms persistence."""
    api.deliver(envelope)
    queue.delete(envelope['msg_id'])
