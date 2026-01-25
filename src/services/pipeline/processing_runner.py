from __future__ import annotations

import os
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Callable, Optional

from src.core.config import Config
from src.core.logger import logger
from src.domain.interfaces.database import BaseDB
from src.domain.tasks.models import Task
try:  # pragma: no cover - optional heavy dependencies
    from src.infrastructure.llm.summarizer_service import Summarizer
except ModuleNotFoundError:  # pragma: no cover - testing scaffold
    Summarizer = None  # type: ignore

try:  # pragma: no cover - optional heavy dependencies
    from src.infrastructure.media.downloader import YouTubeDownloader
except ModuleNotFoundError:  # pragma: no cover - testing scaffold
    YouTubeDownloader = None  # type: ignore

try:  # pragma: no cover - optional heavy dependencies
    from src.infrastructure.media.transcription.transcriber import Transcriber
except ModuleNotFoundError:  # pragma: no cover - testing scaffold
    Transcriber = None  # type: ignore

from src.infrastructure.notifications.discord import (
    send_task_completion_notification,
)
from src.infrastructure.persistence.factory import DBFactory
from src.infrastructure.storage.file_storage import FileManager

try:  # pragma: no cover - optional heavy dependencies
    from src.infrastructure.storage.summary_storage import SummaryStorage
except ModuleNotFoundError:  # pragma: no cover - testing scaffold
    SummaryStorage = None  # type: ignore
from src.services.outputs.path_builder import build_summary_output_path


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


DownloaderFactory = Callable[[str, str], YouTubeDownloader]
TranscriberFactory = Callable[[str], Transcriber]
SummarizerFactory = Callable[[], Summarizer]
SummaryStorageFactory = Callable[[], SummaryStorage]
FileManagerFactory = Callable[[], FileManager]
NotifierFunc = Callable[..., bool]
ConfigFactory = Callable[[], Config]


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
        downloader_factory: Optional[DownloaderFactory] = None,
        transcriber_factory: Optional[TranscriberFactory] = None,
        summarizer_factory: Optional[SummarizerFactory] = None,
        summary_storage_factory: Optional[SummaryStorageFactory] = None,
        file_manager_factory: Optional[FileManagerFactory] = None,
        notifier: Optional[NotifierFunc] = None,
        config_factory: Optional[ConfigFactory] = None,
    ):
        self.db = db
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex}"
        self.task_lock_timeout_seconds = task_lock_timeout_seconds
        self.processing_lock_timeout_seconds = processing_lock_timeout_seconds
        self.lock_refresh_interval = lock_refresh_interval
        self.config = (config_factory or Config)()
        if downloader_factory is not None:
            self.downloader_factory = downloader_factory
        else:
            if YouTubeDownloader is None:
                raise RuntimeError(
                    "YouTube downloader dependency missing. Install yt-dlp-related extras."
                )
            self.downloader_factory = lambda url, output_path: YouTubeDownloader(  # type: ignore[misc]
                url, output_path=output_path
            )
        if transcriber_factory is not None:
            self.transcriber_factory = transcriber_factory
        else:
            if Transcriber is None:
                raise RuntimeError(
                    "Transcriber dependency missing. Install faster-whisper or provide a custom factory."
                )
            self.transcriber_factory = lambda model_size: Transcriber(  # type: ignore[misc]
                model_size=model_size
            )
        if summarizer_factory is not None:
            self.summarizer_factory = summarizer_factory
        else:
            if Summarizer is None:
                raise RuntimeError(
                    "Summarizer dependency missing. Install LLM dependencies or provide a custom factory."
                )
            self.summarizer_factory = Summarizer  # type: ignore[assignment]
        if summary_storage_factory is not None:
            self.summary_storage_factory = summary_storage_factory
        else:
            if SummaryStorage is None:
                raise RuntimeError(
                    "Summary storage dependency missing. Install Notion client or provide a custom factory."
                )
            self.summary_storage_factory = SummaryStorage  # type: ignore[assignment]
        self.file_manager_factory = file_manager_factory or FileManager
        self.notifier = notifier or send_task_completion_notification

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
            previous_title = task.title
            task.title = download_result.get("title") or task.title or task.url
            logger.info(
                f"Resolved task title={task.title} (download_title={download_result.get('title')}, previous_title={previous_title})"
            )

            # Persist the resolved title while keeping status in Processing.
            self.db.update_task_status(task.id, "Processing", title=task.title)

            cfg = self.config
            transcriber = self.transcriber_factory(cfg.transcription_model_size)
            transcription_text = transcriber.transcribe(file_path)

            summarizer = self.summarizer_factory()
            summarized_text = summarizer.summarize(task.title, transcription_text)

            summarizer_label = getattr(summarizer, "last_model_label", "unknown")
            model_label = f"faster-whisper-{cfg.transcription_model_size}+{summarizer_label}"

            output_file = build_summary_output_path(task.title, task.url)
            file_manager = self.file_manager_factory()
            file_manager.save_text(summarized_text, output_file)

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
    return DBFactory.get_db(resolved_type)


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
