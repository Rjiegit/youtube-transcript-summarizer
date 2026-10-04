"""Interchangeable processing engines for the media pipeline."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Callable, Protocol, TypedDict

from whisper_summary.core.logger import logger
from whisper_summary.domain.interfaces.database import BaseDB
from whisper_summary.domain.media.models import VideoMetadata
from whisper_summary.domain.tasks.models import Task
from whisper_summary.services.outputs.path_builder import build_summary_output_path


LEGACY_ENGINE = "legacy"
LANGGRAPH_ENGINE = "langgraph"
SUPPORTED_PROCESSING_ENGINES = {LEGACY_ENGINE, LANGGRAPH_ENGINE}


def normalize_processing_engine(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    normalized = value.strip().lower()
    if normalized not in SUPPORTED_PROCESSING_ENGINES:
        choices = ", ".join(sorted(SUPPORTED_PROCESSING_ENGINES))
        raise ValueError(f"Unsupported processing engine: {value}. Expected one of: {choices}.")
    return normalized


def resolve_processing_engine(task_override: str | None, configured_default: str | None) -> str:
    """Resolve task override first, then configured default, then legacy."""
    return (
        normalize_processing_engine(task_override)
        or normalize_processing_engine(configured_default)
        or LEGACY_ENGINE
    )


class PipelineState(TypedDict, total=False):
    task_id: str
    url: str
    title: str
    start_time: float
    file_path: str
    metadata: VideoMetadata | None
    transcription_text: str
    summarized_text: str
    model_label: str
    output_file: str
    notion_page_id: str | None
    processing_duration: float
    processing_engine: str
    persist_processing_engine: bool


@dataclass(frozen=True)
class PipelineRuntime:
    db: BaseDB
    config: object
    downloader_factory: Callable
    transcriber_factory: Callable
    summarizer_factory: Callable
    summary_storage_factory: Callable
    file_manager_factory: Callable
    notifier: Callable


@dataclass(frozen=True)
class ProcessingResult:
    title: str
    summary: str
    model_label: str
    notion_page_id: str | None
    processing_duration: float


class ProcessingEngine(Protocol):
    def execute(self, task: Task) -> ProcessingResult: ...


class PipelineOperations:
    """The behavior shared by both orchestration engines."""

    def __init__(self, runtime: PipelineRuntime):
        self.runtime = runtime

    @staticmethod
    def initial_state(task: Task, engine_name: str) -> PipelineState:
        return {
            "task_id": task.id,
            "url": task.url,
            "title": task.title,
            "start_time": time.time(),
            "notion_page_id": task.notion_page_id,
            "processing_engine": engine_name,
            "persist_processing_engine": task.processing_engine is not None,
        }

    def download_media(self, state: PipelineState) -> dict:
        cfg = self.runtime.config
        downloader = self.runtime.downloader_factory(state["url"], cfg.data_dir)
        download_result = downloader.download()
        metadata = download_result.get("metadata")
        if not isinstance(metadata, VideoMetadata):
            metadata = None
        previous_title = state["title"]
        title = download_result.get("title") or previous_title or state["url"]
        logger.info(
            f"Resolved task title={title} "
            f"(download_title={download_result.get('title')}, "
            f"previous_title={previous_title})"
        )
        return {
            "file_path": download_result["path"],
            "metadata": metadata,
            "title": title,
        }

    def persist_resolved_title(self, state: PipelineState) -> dict:
        update_kwargs = {"title": state["title"]}
        if state["persist_processing_engine"]:
            update_kwargs["processing_engine"] = state["processing_engine"]
        self.runtime.db.update_task_status(
            state["task_id"],
            "Processing",
            **update_kwargs,
        )
        return {}

    def transcribe_media(self, state: PipelineState) -> dict:
        transcriber = self.runtime.transcriber_factory(
            self.runtime.config.transcription_model_size
        )
        return {"transcription_text": transcriber.transcribe(state["file_path"])}

    def summarize_transcript(self, state: PipelineState) -> dict:
        summarizer = self.runtime.summarizer_factory()
        metadata = state.get("metadata")
        if metadata is None:
            summarized_text = summarizer.summarize(
                state["title"],
                state["transcription_text"],
            )
        else:
            summarized_text = summarizer.summarize(
                state["title"],
                state["transcription_text"],
                metadata,
            )
        summarizer_label = getattr(summarizer, "last_model_label", "unknown")
        return {
            "summarized_text": summarized_text,
            "model_label": (
                f"faster-whisper-{self.runtime.config.transcription_model_size}"
                f"+{summarizer_label}"
            ),
        }

    def save_local_artifacts(self, state: PipelineState) -> dict:
        output_file = build_summary_output_path(state["title"], state["url"])
        file_manager = self.runtime.file_manager_factory()
        summary_file_result = file_manager.save_text(
            state["summarized_text"],
            output_file,
        )
        metadata = state.get("metadata")
        if metadata is not None:
            saved_summary_path = output_file
            if isinstance(summary_file_result, dict):
                result_path = summary_file_result.get("path")
                if isinstance(result_path, str) and result_path:
                    saved_summary_path = result_path
            metadata_output_file = os.path.splitext(saved_summary_path)[0] + ".metadata.json"
            try:
                file_manager.save_json(metadata.to_dict(), metadata_output_file)
            except Exception as exc:
                logger.warning(
                    "Could not save video metadata sidecar for "
                    f"task {state['task_id']}: {exc}"
                )
        return {"output_file": output_file}

    def publish_summary(self, state: PipelineState) -> dict:
        storage_result = self.runtime.summary_storage_factory().save(
            title=state["title"],
            text=state["summarized_text"],
            model=state["model_label"],
            url=state["url"],
        )
        notion_page_id = state.get("notion_page_id")
        if isinstance(storage_result, dict) and storage_result.get("page_id"):
            notion_page_id = str(storage_result["page_id"])
        return {"notion_page_id": notion_page_id}

    def complete_task(self, state: PipelineState) -> dict:
        duration = time.time() - state["start_time"]
        self.runtime.db.update_task_status(
            state["task_id"],
            "Completed",
            title=state["title"],
            summary=state["summarized_text"],
            processing_duration=duration,
            notion_page_id=state.get("notion_page_id"),
        )
        return {"processing_duration": duration}

    def send_notification(self, state: PipelineState) -> dict:
        self.runtime.notifier(
            state["title"] or "untitled",
            state["url"],
            self.runtime.config.discord_webhook_url,
            notion_task_id=state.get("notion_page_id"),
            showcase_base_url=self.runtime.config.showcase_base_url,
        )
        return {}

    @staticmethod
    def result(state: PipelineState) -> ProcessingResult:
        return ProcessingResult(
            title=state["title"],
            summary=state["summarized_text"],
            model_label=state["model_label"],
            notion_page_id=state.get("notion_page_id"),
            processing_duration=state["processing_duration"],
        )


class LegacyProcessingEngine:
    def __init__(self, runtime: PipelineRuntime):
        self.operations = PipelineOperations(runtime)

    def execute(self, task: Task) -> ProcessingResult:
        state = self.operations.initial_state(task, LEGACY_ENGINE)
        for operation in (
            self.operations.download_media,
            self.operations.persist_resolved_title,
            self.operations.transcribe_media,
            self.operations.summarize_transcript,
            self.operations.save_local_artifacts,
            self.operations.publish_summary,
            self.operations.complete_task,
            self.operations.send_notification,
        ):
            state.update(operation(state))
        return self.operations.result(state)


def create_processing_engine(engine_name: str, runtime: PipelineRuntime) -> ProcessingEngine:
    normalized = normalize_processing_engine(engine_name)
    if normalized == LEGACY_ENGINE:
        return LegacyProcessingEngine(runtime)
    if normalized == LANGGRAPH_ENGINE:
        from whisper_summary.services.pipeline.langgraph_engine import LangGraphProcessingEngine

        return LangGraphProcessingEngine(runtime)
    raise ValueError("A processing engine is required.")
