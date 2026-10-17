"""Deliver cloud submissions to the local Task API before acknowledging them."""
import argparse
import logging
import math
import os
import threading

from whisper_summary.infrastructure.task_queue.supabase_inbox import InboxTransportError, SupabaseInbox
from whisper_summary.infrastructure.task_queue.video_inbox_api import InboxApiError, VideoInboxApi
from whisper_summary.services.tasks.video_inbox import receive_message

log = logging.getLogger(__name__)


def run_forever(api, queue, *, idle_seconds=300, batch_limit=20, stop_event=None):
    if not math.isfinite(idle_seconds) or idle_seconds <= 0 or batch_limit <= 0:
        raise ValueError('Invalid polling settings')
    stopper = stop_event or threading.Event()
    failures = 0
    while not stopper.is_set():
        try:
            for _ in range(batch_limit):
                if stopper.is_set():
                    return
                messages = queue.read()
                if not messages:
                    break
                for message in messages:
                    receive_message(api, queue, message)
            failures = 0
            delay = idle_seconds if not messages else 0.1
        except Exception as exc:
            failures = min(failures + 1, 7)
            delay = min(300, 5 * 2 ** (failures - 1))
            category = exc.category if isinstance(exc, (InboxTransportError, InboxApiError)) else 'unexpected'
            status = exc.status if isinstance(exc, (InboxTransportError, InboxApiError)) else None
            log.warning('Video inbox cycle failed category=%s status=%s retry_seconds=%s', category, status, delay)
        stopper.wait(delay)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--idle-seconds', type=float, default=float(os.getenv('VIDEO_INBOX_IDLE_SECONDS', '300')))
    parser.add_argument('--batch-limit', type=int, default=int(os.getenv('VIDEO_INBOX_BATCH_LIMIT', '20')))
    args = parser.parse_args()
    queue = SupabaseInbox(os.environ['VIDEO_INBOX_SUPABASE_URL'], os.environ['VIDEO_INBOX_PUBLISHABLE_KEY'],
                          os.environ['VIDEO_INBOX_RECEIVER_TOKEN'])
    logging.basicConfig(level=logging.INFO)
    worker_token = os.getenv('PROCESSING_WORKER_TOKEN') or os.getenv('PROCESSING_LOCK_ADMIN_TOKEN')
    api = VideoInboxApi(os.getenv('TASK_API_BASE_URL', 'http://localhost:8080'), worker_token)
    run_forever(api, queue, idle_seconds=args.idle_seconds, batch_limit=args.batch_limit)


if __name__ == '__main__':
    main()
