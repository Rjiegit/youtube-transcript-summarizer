import unittest
from dataclasses import replace
from functools import partial
from types import SimpleNamespace
from unittest.mock import MagicMock, call

from whisper_summary.domain.tasks.models import Task
from whisper_summary.infrastructure.notifications.discord import send_task_completion_notification
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
    SUMMARY_PAGE_ID = "12345678-1234-1234-1234-1234567890ab"

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
            events.append("publish") or {"page_id": self.SUMMARY_PAGE_ID}
        )
        notifier = MagicMock(side_effect=lambda *_args, **_kwargs: events.append("notify") or True)

        runtime = PipelineRuntime(
            db=db,
            config=SimpleNamespace(
                data_dir="data",
                transcription_model_size="tiny",
                discord_webhook_url=None,
                notion_url=None,
                showcase_base_url="https://knowledge.example.com",
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
                self.assertEqual(result.notion_page_id, self.SUMMARY_PAGE_ID)
                runtime.notifier.assert_called_once_with(
                    "Title", "https://youtu.be/example", None,
                    notion_task_id=self.SUMMARY_PAGE_ID,
                    showcase_base_url="https://knowledge.example.com",
                )
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
                            notion_page_id=self.SUMMARY_PAGE_ID,
                        ),
                    ],
                )

    def test_both_engines_send_only_knowledge_link_with_notion_configured(self):
        for engine_name in (LEGACY_ENGINE, LANGGRAPH_ENGINE):
            with self.subTest(engine=engine_name):
                runtime, _events = self._runtime()
                runtime.config.notion_url = "https://www.notion.so/workspace"
                runtime.config.discord_webhook_url = "https://discord.example/webhook"
                post = MagicMock(return_value=SimpleNamespace(status_code=204))
                runtime = replace(runtime, notifier=partial(send_task_completion_notification, post=post))
                task = Task(id="1", url="https://youtu.be/example", status="Processing")

                create_processing_engine(engine_name, runtime).execute(task)

                post.assert_called_once_with(
                    "https://discord.example/webhook",
                    json={"content": (
                        "✅ 任務完成：Title\nhttps://youtu.be/example\n"
                        f"知識庫：https://knowledge.example.com/results/{self.SUMMARY_PAGE_ID}"
                    )},
                    timeout=10,
                )
                self.assertEqual(
                    runtime.db.update_task_status.call_args.kwargs["notion_page_id"],
                    self.SUMMARY_PAGE_ID,
                )

    def test_both_engines_do_not_fall_back_to_notion_without_knowledge_url(self):
        for engine_name in (LEGACY_ENGINE, LANGGRAPH_ENGINE):
            with self.subTest(engine=engine_name):
                runtime, _events = self._runtime()
                runtime.config.notion_url = "https://www.notion.so/workspace"
                runtime.config.discord_webhook_url = "https://discord.example/webhook"
                runtime.config.showcase_base_url = None
                post = MagicMock(return_value=SimpleNamespace(status_code=204))
                runtime = replace(runtime, notifier=partial(send_task_completion_notification, post=post))
                task = Task(id="1", url="https://youtu.be/example", status="Processing")

                create_processing_engine(engine_name, runtime).execute(task)

                post.assert_called_once_with(
                    "https://discord.example/webhook",
                    json={"content": (
                        "✅ 任務完成：Title\nhttps://youtu.be/example"
                    )},
                    timeout=10,
                )
                self.assertEqual(
                    runtime.db.update_task_status.call_args.kwargs["notion_page_id"],
                    self.SUMMARY_PAGE_ID,
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
