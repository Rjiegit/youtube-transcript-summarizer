import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, call

from whisper_summary.domain.tasks.models import Task
from whisper_summary.services.pipeline.engines import (
    LANGGRAPH_ENGINE,
    LEGACY_ENGINE,
    PipelineRuntime,
    create_processing_engine,
    resolve_processing_engine,
)


class TestProcessingEngineSelection(unittest.TestCase):
    def test_task_override_takes_precedence_over_default(self):
        self.assertEqual(
            resolve_processing_engine("langgraph", "legacy"),
            LANGGRAPH_ENGINE,
        )

    def test_missing_override_uses_configured_default(self):
        self.assertEqual(
            resolve_processing_engine(None, "langgraph"),
            LANGGRAPH_ENGINE,
        )

    def test_invalid_engine_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "processing engine"):
            resolve_processing_engine("unknown", "legacy")


class TestProcessingEngineParity(unittest.TestCase):
    def _runtime(self):
        events = []
        db = MagicMock()

        downloader = MagicMock()
        downloader.download.side_effect = lambda: (
            events.append("download")
            or {"path": "/tmp/audio.wav", "title": "Title"}
        )
        transcriber = MagicMock()
        transcriber.transcribe.side_effect = lambda _path: (
            events.append("transcribe") or "transcript"
        )
        summarizer = MagicMock()
        summarizer.summarize.side_effect = lambda *_args: (
            events.append("summarize") or "summary"
        )
        summarizer.last_model_label = "openai:test"
        file_manager = MagicMock()
        file_manager.save_text.side_effect = lambda *_args: events.append("save_file")
        storage = MagicMock()
        storage.save.side_effect = lambda **_kwargs: (
            events.append("publish") or {"page_id": "page-1"}
        )
        notifier = MagicMock(side_effect=lambda *_args, **_kwargs: events.append("notify") or True)

        runtime = PipelineRuntime(
            db=db,
            config=SimpleNamespace(
                data_dir="data",
                transcription_model_size="tiny",
                discord_webhook_url=None,
                notion_url=None,
            ),
            downloader_factory=lambda *_args: downloader,
            transcriber_factory=lambda *_args: transcriber,
            summarizer_factory=lambda: summarizer,
            summary_storage_factory=lambda: storage,
            file_manager_factory=lambda: file_manager,
            notifier=notifier,
        )
        return runtime, events

    def test_legacy_and_langgraph_have_the_same_observable_contract(self):
        expected_events = [
            "download",
            "transcribe",
            "summarize",
            "save_file",
            "publish",
            "notify",
        ]

        for engine_name in (LEGACY_ENGINE, LANGGRAPH_ENGINE):
            with self.subTest(engine=engine_name):
                runtime, events = self._runtime()
                task = Task(
                    id="1",
                    url="https://youtu.be/example",
                    status="Processing",
                    processing_engine=engine_name,
                )

                result = create_processing_engine(engine_name, runtime).execute(task)

                self.assertEqual(events, expected_events)
                self.assertEqual(result.title, "Title")
                self.assertEqual(result.summary, "summary")
                self.assertEqual(result.notion_page_id, "page-1")
                self.assertEqual(result.model_label, "faster-whisper-tiny+openai:test")
                self.assertEqual(
                    runtime.db.update_task_status.call_args_list,
                    [
                        call(
                            "1",
                            "Processing",
                            title="Title",
                            processing_engine=engine_name,
                        ),
                        call(
                            "1",
                            "Completed",
                            title="Title",
                            summary="summary",
                            processing_duration=result.processing_duration,
                            notion_page_id="page-1",
                        ),
                    ],
                )

    def test_system_default_does_not_require_persisted_engine_property(self):
        runtime, _events = self._runtime()
        task = Task(id="1", url="https://youtu.be/example", status="Processing")

        create_processing_engine(LEGACY_ENGINE, runtime).execute(task)

        self.assertEqual(
            runtime.db.update_task_status.call_args_list[0],
            call("1", "Processing", title="Title"),
        )


if __name__ == "__main__":
    unittest.main()
