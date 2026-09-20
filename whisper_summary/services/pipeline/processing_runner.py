from __future__ import annotations

import os
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from whisper_summary.core.logger import logger
from whisper_summary.domain.interfaces.database import BaseDB
from whisper_summary.domain.tasks.models import Task
from whisper_summary.services.pipeline.engines import (
    LEGACY_ENGINE,
    PipelineRuntime,
    create_processing_engine,
    resolve_processing_engine,
)
from whisper_summary.services.pipeline.dependencies import ProcessingDependencies


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
        self.pipeline_runtime = PipelineRuntime(
            db=self.db,
            config=self.config,
            downloader_factory=self.downloader_factory,
            transcriber_factory=self.transcriber_factory,
            summarizer_factory=self.summarizer_factory,
            summary_storage_factory=self.summary_storage_factory,
            file_manager_factory=self.file_manager_factory,
            notifier=self.notifier,
        )
        self._processing_engines = {}

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
            engine_name = resolve_processing_engine(
                task.processing_engine,
                getattr(self.config, "processing_engine", LEGACY_ENGINE),
            )
            logger.info(
                f"Worker {self.worker_id} selected {engine_name} engine "
                f"for task {task.id}"
            )
            engine = self._processing_engines.get(engine_name)
            if engine is None:
                engine = create_processing_engine(engine_name, self.pipeline_runtime)
                self._processing_engines[engine_name] = engine
            result = engine.execute(task)
            task.title = result.title
            task.summary = result.summary
            task.notion_page_id = result.notion_page_id
            duration = result.processing_duration
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
