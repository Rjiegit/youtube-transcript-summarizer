"""The local API owns durable inbox delivery before cloud acknowledgement."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from whisper_summary.apps.api.main import app
from whisper_summary.infrastructure.persistence.sqlite.client import SQLiteDB


class VideoInboxApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = SQLiteDB(str(Path(self.temp.name) / 'tasks.db'))
        self.client = TestClient(app)
        self.envelope = {'msg_id': 7, 'message': {
            'version': 1, 'submission_id': str(uuid4()), 'url': 'https://youtu.be/dQw4w9WgXcQ',
        }}
        self.token = patch.dict(os.environ, {'PROCESSING_WORKER_TOKEN': 'worker-secret'})
        self.token.start()
        self.addCleanup(self.token.stop)
        self.database = patch('whisper_summary.apps.api.routers.video_inbox.get_database', return_value=self.db)
        self.database.start()
        self.addCleanup(self.database.stop)

    def post(self, envelope=None, token='worker-secret'):
        headers = {'X-Worker-Token': token} if token is not None else {}
        return self.client.post('/video-inbox/messages', json=envelope or self.envelope, headers=headers)

    def test_requires_worker_token(self):
        self.assertEqual(self.post(token=None).status_code, 401)
        self.assertEqual(self.post(token='wrong').status_code, 403)
        self.assertEqual(self.db.get_all_tasks(), [])

    def test_accepts_and_deduplicates_same_submission(self):
        self.assertEqual(self.post().json()['outcome'], 'accepted')
        self.assertEqual(self.post().json()['outcome'], 'accepted')
        self.assertEqual(len(self.db.get_all_tasks()), 1)
        with self.db._get_connection() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM video_inbox_receipts').fetchone()[0], 1)

    def test_invalid_payload_is_quarantined(self):
        response = self.post({'msg_id': 8, 'message': {'version': 99}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['outcome'], 'quarantined')
        self.assertEqual(self.post({'msg_id': 9}).json()['outcome'], 'quarantined')
        with self.db._get_connection() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM video_inbox_quarantine').fetchone()[0], 2)

    def test_local_transaction_failure_does_not_report_success(self):
        with self.db._get_connection() as conn:
            conn.execute("CREATE TRIGGER reject_receipt BEFORE INSERT ON video_inbox_receipts "
                         "BEGIN SELECT RAISE(ABORT, 'injected'); END")
        response = self.post()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.db.get_all_tasks(), [])
