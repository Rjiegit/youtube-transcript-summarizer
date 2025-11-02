from __future__ import annotations

import os
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from config import Config
from database.database_interface import BaseDB
from database.db_factory import DBFactory
from database.task import Task
from file_manager import FileManager
from discord_notifier import send_task_completion_notification
from logger import logger
from url_validator import extract_video_id

try:  # pragma: no cover - optional heavy dependencies
    from summarizer import Summarizer
except ModuleNotFoundError:  # pragma: no cover - testing scaffold
    Summarizer = None  # type: ignore

try:  # pragma: no cover - optional heavy dependencies
    from summary_storage import SummaryStorage
except ModuleNotFoundError:  # pragma: no cover - testing scaffold
    SummaryStorage = None  # type: ignore

try:  # pragma: no cover - optional heavy dependencies
    from transcriber import Transcriber
except ModuleNotFoundError:  # pragma: no cover - testing scaffold
    Transcriber = None  # type: ignore

try:  # pragma: no cover - optional heavy dependencies
    from youtube_downloader import YouTubeDownloader
except ModuleNotFoundError:  # pragma: no cover - testing scaffold
    YouTubeDownloader = None  # type: ignore


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
        *,
        worker_id: Optional[str] = None,
        task_lock_timeout_seconds: int = TASK_LOCK_TIMEOUT_SECONDS,
        processing_lock_timeout_seconds: int = PROCESSING_LOCK_TIMEOUT_SECONDS,
        lock_refresh_interval: int = PROCESSING_LOCK_REFRESH_INTERVAL,
    ):
        self.db = db
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex}"
        self.task_lock_timeout_seconds = task_lock_timeout_seconds
        self.processing_lock_timeout_seconds = processing_lock_timeout_seconds
        self.lock_refresh_interval = lock_refresh_interval

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
            if None in (YouTubeDownloader, Transcriber, Summarizer, SummaryStorage):
                raise RuntimeError(
                    "Processing dependencies are missing. Please install optional transcription/summarization packages."
                )

            downloader = YouTubeDownloader(task.url, output_path="data")
            download_result = downloader.download()
            file_path = download_result["path"]
            task.title = download_result.get("title") or task.title or task.url

            # Persist the resolved title while keeping status in Processing.
            self.db.update_task_status(task.id, "Processing", title=task.title)

            cfg = Config()
            transcriber = Transcriber(model_size=cfg.transcription_model_size)
            transcription_text = transcriber.transcribe(file_path)

            summarizer = Summarizer()
            summarized_text = summarizer.summarize(task.title, transcription_text)

            summarizer_label = getattr(summarizer, "last_model_label", "unknown")
            model_label = f"faster-whisper-{cfg.transcription_model_size}+{summarizer_label}"

            output_file = build_summary_output_path(task.title, task.url)
            FileManager.save_text(summarized_text, output_file)

            SummaryStorage().save(
                title=task.title,
                text=summarized_text,
                model=model_label,
                url=task.url,
            )

            duration = time.time() - start_time
            self.db.update_task_status(
                task.id,
                "Completed",
                title=task.title,
                summary=summarized_text,
                processing_duration=duration,
            )
            send_task_completion_notification(
                task.title or "untitled",
                task.url,
                cfg.discord_webhook_url,
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


def build_summary_output_path(title: str, url: str, now: float | None = None) -> str:
    """Build a unique output path for the summary file."""
    ts = time.strftime(
        "%Y%m%d%H%M%S", time.localtime(now) if now is not None else time.localtime()
    )
    video_id = extract_video_id(url) or "noid"
    sanitized_title = FileManager.sanitize_filename(title or "untitled")
    filename = f"_summarized_{ts}_{video_id}_{sanitized_title}.md"
    return os.path.join("data", "summaries", filename)


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
