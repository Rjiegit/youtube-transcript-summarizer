import os
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

# Provide lightweight stubs for optional dependencies when running in minimal envs.
if "pytz" not in sys.modules:  # pragma: no cover - testing scaffold
    pytz_stub = types.ModuleType("pytz")

    def _fake_timezone(_name: str):
        class _FakeTZ:
            def localize(self, value):
                return value

        return _FakeTZ()

    pytz_stub.timezone = _fake_timezone
    sys.modules["pytz"] = pytz_stub

if "notion_client" not in sys.modules:  # pragma: no cover - testing scaffold
    notion_stub = types.ModuleType("notion_client")

    class _Client:  # minimal stub
        def __init__(self, *_, **__):
            pass

    notion_stub.Client = _Client
    sys.modules["notion_client"] = notion_stub

from database.sqlite_client import SQLiteDB
from processing import ProcessingWorker


class TestProcessingWorker(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        self.db = SQLiteDB(db_path=self.tmp.name)

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except FileNotFoundError:
            pass

    @patch("processing.Config")
    @patch("processing.send_task_completion_notification")
    @patch("processing.SummaryStorage")
    @patch("processing.FileManager.save_text")
    @patch("processing.Summarizer")
    @patch("processing.Transcriber")
    @patch("processing.YouTubeDownloader")
    def test_worker_processes_all_tasks(
        self,
        mock_downloader,
        mock_transcriber,
        mock_summarizer,
        mock_save_text,
        mock_summary_storage,
        mock_notify,
        mock_config,
    ):
        first_task = self.db.add_task("https://youtu.be/alpha")
        second_task = self.db.add_task("https://youtu.be/bravo")

        downloader_instance = mock_downloader.return_value
        downloader_instance.download.return_value = {
            "path": "/tmp/audio.wav",
            "title": "Sample Title",
        }

        transcriber_instance = mock_transcriber.return_value
        transcriber_instance.transcribe.return_value = "transcription text"

        summarizer_instance = mock_summarizer.return_value
        summarizer_instance.summarize.return_value = "summary"
        summarizer_instance.last_model_label = "gpt"

        mock_save_text.return_value = None
        mock_summary_storage.return_value.save.side_effect = [
            {"page_id": "11111111-2222-3333-4444-555555555555"},
            {"page_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"},
        ]
        mock_config.return_value = types.SimpleNamespace(
            transcription_model_size="tiny",
            notion_url=None,
            discord_webhook_url=None,
        )
        mock_notify.return_value = True

        worker = ProcessingWorker(
            self.db,
            worker_id="worker-test",
            task_lock_timeout_seconds=1,
            processing_lock_timeout_seconds=5,
            lock_refresh_interval=1,
        )
        summary = worker.run()

        self.assertTrue(summary.acquired_lock)
        self.assertEqual(summary.processed_tasks, 2)
        self.assertEqual(summary.failed_tasks, 0)

        tasks = self.db.get_all_tasks()
        self.assertTrue(all(task.status == "Completed" for task in tasks))
        notion_ids = {task.id: task.notion_page_id for task in tasks}
        self.assertEqual(
            notion_ids.get(first_task.id),
            "11111111-2222-3333-4444-555555555555",
        )
        self.assertEqual(
            notion_ids.get(second_task.id),
            "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        )
        self.assertEqual(mock_save_text.call_count, 2)
        self.assertEqual(mock_summary_storage.return_value.save.call_count, 2)
        self.assertEqual(mock_notify.call_count, 2)
        mock_notify.assert_any_call(
            "Sample Title",
            "https://youtu.be/alpha",
            None,
            notion_url=None,
            notion_task_id="11111111-2222-3333-4444-555555555555",
        )
        mock_notify.assert_any_call(
            "Sample Title",
            "https://youtu.be/bravo",
            None,
            notion_url=None,
            notion_task_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        )

    @patch("processing.Config")
    @patch("processing.send_task_completion_notification")
    @patch("processing.SummaryStorage")
    @patch("processing.FileManager.save_text")
    @patch("processing.Summarizer")
    @patch("processing.Transcriber")
    @patch("processing.YouTubeDownloader")
    def test_worker_continues_after_failure(
        self,
        mock_downloader,
        mock_transcriber,
        mock_summarizer,
        mock_save_text,
        mock_summary_storage,
        mock_notify,
        mock_config,
    ):
        first_task = self.db.add_task("https://youtu.be/charlie")
        second_task = self.db.add_task("https://youtu.be/delta")

        downloader_instance = mock_downloader.return_value
        downloader_instance.download.side_effect = [
            Exception("download failed"),
            {"path": "/tmp/audio.wav", "title": "Recovered Title"},
        ]

        transcriber_instance = mock_transcriber.return_value
        transcriber_instance.transcribe.return_value = "transcription text"

        summarizer_instance = mock_summarizer.return_value
        summarizer_instance.summarize.return_value = "summary"
        summarizer_instance.last_model_label = "gpt"

        mock_save_text.return_value = None
        mock_summary_storage.return_value.save.return_value = {
            "page_id": "ffffffff-1111-2222-3333-444444444444"
        }
        mock_config.return_value = types.SimpleNamespace(
            transcription_model_size="tiny",
            notion_url=None,
            discord_webhook_url=None,
        )
        mock_notify.return_value = True

        worker = ProcessingWorker(
            self.db,
            worker_id="worker-retry",
            task_lock_timeout_seconds=1,
            processing_lock_timeout_seconds=5,
            lock_refresh_interval=1,
        )
        summary = worker.run()

        self.assertTrue(summary.acquired_lock)
        self.assertEqual(summary.processed_tasks, 1)
        self.assertEqual(summary.failed_tasks, 1)

        failed = self.db.get_task_by_id(first_task.id)
        succeeded = self.db.get_task_by_id(second_task.id)
        self.assertEqual(failed.status, "Failed")
        self.assertEqual(succeeded.status, "Completed")
        self.assertEqual(
            succeeded.notion_page_id,
            "ffffffff-1111-2222-3333-444444444444",
        )

        self.assertEqual(mock_save_text.call_count, 1)
        self.assertEqual(mock_summary_storage.return_value.save.call_count, 1)
        mock_notify.assert_called_once_with(
            "Recovered Title",
            "https://youtu.be/delta",
            None,
            notion_url=None,
            notion_task_id="ffffffff-1111-2222-3333-444444444444",
        )


if __name__ == "__main__":
    unittest.main()
