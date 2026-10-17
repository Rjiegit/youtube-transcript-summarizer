"""Transaction-scoped repository for the existing task creation policy."""
import sqlite3

from whisper_summary.services.tasks.task_creation import create_task_record
from whisper_summary.services.tasks.video_inbox import validate_message


class TransactionTasks:
    def __init__(self, conn, adapter):
        self.conn = conn
        self.adapter = adapter

    def find_recent_task_by_url(self, url):
        row = self.conn.execute(
            "SELECT * FROM tasks WHERE url = ? AND status NOT IN ('Failed', 'Failed Retry Created') "
            "ORDER BY created_at DESC, id DESC LIMIT 1", (url,),
        ).fetchone()
        return self.adapter.to_task(dict(row)) if row else None

    def add_task(self, url, **kwargs):
        cursor = self.conn.execute(
            "INSERT INTO tasks (url, status, title, source_type, source_channel_id, processing_engine) "
            "VALUES (?, 'Pending', ?, ?, ?, ?)",
            (url, url, kwargs['source_type'], kwargs.get('source_channel_id'), kwargs.get('processing_engine')),
        )
        row = self.conn.execute('SELECT * FROM tasks WHERE id = ?', (cursor.lastrowid,)).fetchone()
        return self.adapter.to_task(dict(row))


def accept_submission(db, message, cache_ttl_seconds):
    submission_id, url = validate_message(message)
    conn = db._get_connection()
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('BEGIN IMMEDIATE')
        existing = conn.execute(
            'SELECT task_id, url FROM video_inbox_receipts WHERE submission_id = ?', (submission_id,),
        ).fetchone()
        if existing:
            if existing['url'] != url:
                raise ValueError('submission_id_conflict')
            return str(existing['task_id'])
        result = create_task_record(
            db=TransactionTasks(conn, db.adapter), url=url, source_type='showcase',
            cache_ttl_seconds=cache_ttl_seconds,
        )
        task_id = str(result.task.id)
        conn.execute('INSERT INTO video_inbox_receipts (submission_id, url, task_id) VALUES (?, ?, ?)',
                     (submission_id, url, task_id))
        conn.commit()
        return task_id
    finally:
        conn.close()
