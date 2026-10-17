"""Receive cloud submissions into the same SQLite database used by the local API."""
import argparse
import sqlite3
import logging
import math
import os
import threading

from whisper_summary.infrastructure.persistence.sqlite.client import SQLiteDB
from whisper_summary.infrastructure.task_queue.supabase_inbox import InboxTransportError, SupabaseInbox
from whisper_summary.services.tasks.video_inbox import receive_message

log = logging.getLogger(__name__)


def run_forever(db, queue, *, idle_seconds=300, batch_limit=20, cache_ttl_seconds=3600, stop_event=None):
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
                    receive_message(db, queue, message, cache_ttl_seconds=cache_ttl_seconds)
            failures = 0
            delay = idle_seconds if not messages else 0.1
        except Exception as exc:
            failures = min(failures + 1, 7)
            delay = min(300, 5 * 2 ** (failures - 1))
            category = exc.category if isinstance(exc, InboxTransportError) else (
                'local_database' if isinstance(exc, sqlite3.Error) else 'unexpected'
            )
            status = exc.status if isinstance(exc, InboxTransportError) else None
            log.warning('Video inbox cycle failed category=%s status=%s retry_seconds=%s', category, status, delay)
        stopper.wait(delay)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db-path', default=os.getenv('VIDEO_INBOX_DB_PATH', 'data/tasks.db'))
    parser.add_argument('--idle-seconds', type=float, default=float(os.getenv('VIDEO_INBOX_IDLE_SECONDS', '300')))
    parser.add_argument('--batch-limit', type=int, default=int(os.getenv('VIDEO_INBOX_BATCH_LIMIT', '20')))
    args = parser.parse_args()
    queue = SupabaseInbox(os.environ['VIDEO_INBOX_SUPABASE_URL'], os.environ['VIDEO_INBOX_PUBLISHABLE_KEY'],
                          os.environ['VIDEO_INBOX_RECEIVER_TOKEN'])
    logging.basicConfig(level=logging.INFO)
    run_forever(SQLiteDB(args.db_path), queue, idle_seconds=args.idle_seconds, batch_limit=args.batch_limit,
                cache_ttl_seconds=int(os.getenv('TASK_CACHE_TTL_SECONDS', '3600')))


if __name__ == '__main__':
    main()
