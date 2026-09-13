from __future__ import annotations

import os
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from whisper_summary.core.logger import logger
from whisper_summary.domain.interfaces.database import BaseDB
from whisper_summary.domain.media.models import VideoMetadata
from whisper_summary.domain.tasks.models import Task
from whisper_summary.services.pipeline.dependencies import ProcessingDependencies
from whisper_summary.services.outputs.path_builder import build_summary_output_path


TASK_LOCK_TIMEOUT_SECONDS = int(os.environ.get("TASK_LOCK_TIMEOUT_SECONDS", "900"))
PROCESSING_LOCK_TIMEOUT_SECONDS = int(
    os.environ.get("PROCESSING_LOCK_TIMEOUT_SECONDS", "1800")
)
PROCESSING_LOCK_REFRESH_INTERVAL = int(
    os.environ.get("PROCESSING_LOCK_REFRESH_INTERVAL", "30")
)


@dataclass
class ProcessingSummary:
    """Aggregated result after running the processing loop."""

    worker_id: str
    processed_tasks: int = 0
    failed_tasks: int = 0
    acquired_lock: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "worker_id": self.worker_id,
            "processed_tasks": self.processed_tasks,
            "failed_tasks": self.failed_tasks,
            "acquired_lock": self.acquired_lock,
        }


class _ProcessingLockRefresher(threading.Thread):
    """Background thread that keeps the global lock alive."""

    def __init__(self, db: BaseDB, worker_id: str, interval_seconds: int):
        super().__init__(daemon=True)
        self._db = db
        self._worker_id = worker_id
        self._interval = max(1, interval_seconds)
        self._stop_event = threading.Event()

    def run(self) -> None:
        while not self._stop_event.wait(self._interval):
            try:
                self._db.refresh_processing_lock(self._worker_id)
            except Exception as exc:
                logger.warning(
                    f"Failed to refresh processing lock for worker {self._worker_id}: {exc}"
                )

    def ping(self) -> None:
        try:
            self._db.refresh_processing_lock(self._worker_id)
        except Exception as exc:
            logger.warning(
                f"Failed to refresh processing lock (manual ping) for worker {self._worker_id}: {exc}"
            )

    def stop(self) -> None:
        self._stop_event.set()
        try:
            self._db.refresh_processing_lock(self._worker_id)
        except Exception as exc:
            logger.warning(
                f"Failed to refresh processing lock on shutdown for worker {self._worker_id}: {exc}"
            )


class ProcessingWorker:
    """Background worker that drains the pending task queue."""

    def __init__(
        self,
        db: BaseDB,
        worker_id: Optional[str] = None,
        task_lock_timeout_seconds: int = TASK_LOCK_TIMEOUT_SECONDS,
        processing_lock_timeout_seconds: int = PROCESSING_LOCK_TIMEOUT_SECONDS,
        lock_refresh_interval: int = PROCESSING_LOCK_REFRESH_INTERVAL,
        *,
        dependencies: ProcessingDependencies | None = None,
        downloader_factory=None,
        transcriber_factory=None,
        summarizer_factory=None,
        summary_storage_factory=None,
        file_manager_factory=None,
        notifier=None,
        config_factory=None,
    ):
        if dependencies is None:
            from whisper_summary.infrastructure.composition import create_processing_dependencies

            dependencies = create_processing_dependencies()
        self.db = db
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex}"
        self.task_lock_timeout_seconds = task_lock_timeout_seconds
        self.processing_lock_timeout_seconds = processing_lock_timeout_seconds
        self.lock_refresh_interval = lock_refresh_interval
        self.config = (config_factory or dependencies.config_factory)()
        self.downloader_factory = downloader_factory or dependencies.downloader_factory
        self.transcriber_factory = transcriber_factory or dependencies.transcriber_factory
        self.summarizer_factory = summarizer_factory or dependencies.summarizer_factory
        self.summary_storage_factory = summary_storage_factory or dependencies.summary_storage_factory
        self.file_manager_factory = file_manager_factory or dependencies.file_manager_factory
        self.notifier = notifier or dependencies.notifier

    def run(self) -> ProcessingSummary:
        """Run the worker loop until no executable tasks remain."""
        summary = ProcessingSummary(worker_id=self.worker_id)
        logger.info(f"Worker {self.worker_id} requesting processing lock")

        if not self.db.acquire_processing_lock(
            self.worker_id, self.processing_lock_timeout_seconds
        ):
            logger.info(
                f"Worker {self.worker_id} could not acquire processing lock; another worker is active."
            )
            return summary

        summary.acquired_lock = True
        refresher = _ProcessingLockRefresher(
            self.db, self.worker_id, self.lock_refresh_interval
        )
        refresher.start()

        try:
            while True:
                try:
                    task = self.db.acquire_next_task(
                        self.worker_id, self.task_lock_timeout_seconds
                    )
                except Exception as exc:  # pragma: no cover - defensive guard
                    logger.error(
                        f"Worker {self.worker_id} encountered an error while acquiring tasks: {exc}"
                    )
                    break

                if task is None:
                    logger.info(f"Worker {self.worker_id} found no pending tasks; exiting.")
                    break

                refresher.ping()
                success = self._process_task(task)
                if success:
                    summary.processed_tasks += 1
                else:
                    summary.failed_tasks += 1
                refresher.ping()

            return summary
        finally:
            refresher.stop()
            self.db.release_processing_lock(self.worker_id)
            logger.info(
                f"Worker {self.worker_id} released processing lock (processed={summary.processed_tasks}, failed={summary.failed_tasks})"
            )

    def _process_task(self, task: Task) -> bool:
        """Execute the full processing pipeline for a task."""
        logger.info(
            f"Worker {self.worker_id} processing task {task.id} ({task.url})"
        )
        start_time = time.time()

        try:
            downloader = self.downloader_factory(task.url, self.config.data_dir)
            download_result = downloader.download()
            file_path = download_result["path"]
            metadata = download_result.get("metadata")
            if not isinstance(metadata, VideoMetadata):
                metadata = None
            previous_title = task.title
            task.title = download_result.get("title") or task.title or task.url
            logger.info(
                f"Resolved task title={task.title} "
                f"(download_title={download_result.get('title')}, "
                f"previous_title={previous_title})"
            )

            # Persist the resolved title while keeping status in Processing.
            self.db.update_task_status(task.id, "Processing", title=task.title)

            cfg = self.config
            transcriber = self.transcriber_factory(cfg.transcription_model_size)
            transcription_text = transcriber.transcribe(file_path)

            summarizer = self.summarizer_factory()
            if metadata is None:
                summarized_text = summarizer.summarize(
                    task.title,
                    transcription_text,
                )
            else:
                summarized_text = summarizer.summarize(
                    task.title,
                    transcription_text,
                    metadata,
                )

            summarizer_label = getattr(summarizer, "last_model_label", "unknown")
            model_label = f"faster-whisper-{cfg.transcription_model_size}+{summarizer_label}"

            output_file = build_summary_output_path(task.title, task.url)
            file_manager = self.file_manager_factory()
            summary_file_result = file_manager.save_text(
                summarized_text,
                output_file,
            )
            if metadata is not None:
                saved_summary_path = output_file
                if isinstance(summary_file_result, dict):
                    result_path = summary_file_result.get("path")
                    if isinstance(result_path, str) and result_path:
                        saved_summary_path = result_path
                metadata_output_file = (
                    os.path.splitext(saved_summary_path)[0]
                    + ".metadata.json"
                )
                try:
                    file_manager.save_json(
                        metadata.to_dict(),
                        metadata_output_file,
                    )
                except Exception as exc:
                    logger.warning(
                        "Could not save video metadata sidecar for "
                        f"task {task.id}: {exc}"
                    )

            notion_page_id: Optional[str] = task.notion_page_id
            summary_storage = self.summary_storage_factory()
            storage_result = summary_storage.save(
                title=task.title,
                text=summarized_text,
                model=model_label,
                url=task.url,
            )

            if isinstance(storage_result, dict):
                raw_page_id = storage_result.get("page_id")
                if raw_page_id:
                    notion_page_id = str(raw_page_id)
                    task.notion_page_id = notion_page_id

            duration = time.time() - start_time
            self.db.update_task_status(
                task.id,
                "Completed",
                title=task.title,
                summary=summarized_text,
                processing_duration=duration,
                notion_page_id=notion_page_id,
            )
            self.notifier(
                task.title or "untitled",
                task.url,
                cfg.discord_webhook_url,
                notion_url=cfg.notion_url,
                notion_task_id=notion_page_id,
            )
            logger.info(
                f"Worker {self.worker_id} completed task {task.id} in {duration:.2f} seconds"
            )
            return True

        except Exception as exc:  # pragma: no cover - the heavy pipeline is mocked in tests
            duration = time.time() - start_time
            logger.error(
                f"Worker {self.worker_id} failed to process task {task.id}: {exc}"
            )
            self.db.update_task_status(
                task.id,
                "Failed",
                error_message=str(exc),
                processing_duration=duration,
            )
            return False


def get_db_client(db_type: Optional[str] = None) -> BaseDB:
    """Return a database client instance based on configuration."""
    resolved_type = (db_type or os.environ.get("DB_TYPE", "sqlite")).lower()
    logger.info(f"Using {resolved_type} database for processing.")
    from whisper_summary.infrastructure.repository_composition import create_database

    return create_database(resolved_type)


def process_pending_tasks(
    *,
    db: Optional[BaseDB] = None,
    worker_id: Optional[str] = None,
    task_lock_timeout_seconds: int = TASK_LOCK_TIMEOUT_SECONDS,
    processing_lock_timeout_seconds: int = PROCESSING_LOCK_TIMEOUT_SECONDS,
    lock_refresh_interval: int = PROCESSING_LOCK_REFRESH_INTERVAL,
) -> ProcessingSummary:
    """Entry point for synchronous processing (Streamlit or scripts)."""
    db_client = db or get_db_client()
    worker = ProcessingWorker(
        db_client,
        worker_id=worker_id,
        task_lock_timeout_seconds=task_lock_timeout_seconds,
        processing_lock_timeout_seconds=processing_lock_timeout_seconds,
        lock_refresh_interval=lock_refresh_interval,
    )
    return worker.run()
