from __future__ import annotations

import os
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from whisper_summary.core.logger import logger
from whisper_summary.domain.ports.task_queue import TaskQueue
from whisper_summary.domain.tasks.leases import TaskLeaseLostError
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
TASK_LEASE_HEARTBEAT_SECONDS = int(
    os.environ.get(
        "TASK_LEASE_HEARTBEAT_SECONDS",
        str(PROCESSING_LOCK_REFRESH_INTERVAL),
    )
)


@dataclass
class ProcessingSummary:
    """Aggregated result after running the processing loop."""

    worker_id: str
    processed_tasks: int = 0
    failed_tasks: int = 0
    lost_leases: int = 0

    def to_dict(self) -> dict[str, object]:
        return {
            "worker_id": self.worker_id,
            "processed_tasks": self.processed_tasks,
            "failed_tasks": self.failed_tasks,
            "lost_leases": self.lost_leases,
        }


class _TaskLeaseRefresher(threading.Thread):
    """Background thread that keeps one claimed task lease alive."""

    def __init__(
        self,
        db: TaskQueue,
        task: Task,
        worker_id: str,
        interval_seconds: int,
    ):
        super().__init__(daemon=True)
        self._db = db
        self._task = task
        self._worker_id = worker_id
        self._interval = max(1, interval_seconds)
        self._stop_event = threading.Event()
        self.lease_lost = threading.Event()

    def _refresh(self) -> None:
        if not self._task.lease_token:
            self.lease_lost.set()
            return
        try:
            refreshed = self._db.refresh_task_lease(
                self._task.id,
                self._worker_id,
                self._task.lease_token,
            )
            if not refreshed:
                self.lease_lost.set()
                logger.error(
                    f"Worker {self._worker_id} lost lease for "
                    f"task {self._task.id}"
                )
        except TaskLeaseLostError:
            self.lease_lost.set()
            logger.error(
                f"Worker {self._worker_id} lost lease for task {self._task.id}"
            )
        except Exception as exc:
            logger.warning(
                f"Failed to refresh task {self._task.id} lease for "
                f"worker {self._worker_id}: {exc}"
            )

    def run(self) -> None:
        while not self._stop_event.wait(self._interval):
            self._refresh()
            if self.lease_lost.is_set():
                return

    def ping(self) -> None:
        self._refresh()

    def stop(self) -> None:
        self._stop_event.set()


class ProcessingWorker:
    """Background worker that drains the pending task queue."""

    def __init__(
        self,
        db: TaskQueue,
        worker_id: Optional[str] = None,
        task_lock_timeout_seconds: int = TASK_LOCK_TIMEOUT_SECONDS,
        task_lease_heartbeat_seconds: int = TASK_LEASE_HEARTBEAT_SECONDS,
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
        self.task_lease_heartbeat_seconds = task_lease_heartbeat_seconds
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
        while True:
            try:
                task = self.db.acquire_next_task(
                    self.worker_id, self.task_lock_timeout_seconds
                )
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.error(
                    f"Worker {self.worker_id} encountered an error while "
                    f"claiming a task: {exc}"
                )
                break

            if task is None:
                logger.info(f"Worker {self.worker_id} found no pending tasks; exiting.")
                break

            refresher = _TaskLeaseRefresher(
                self.db,
                task,
                self.worker_id,
                self.task_lease_heartbeat_seconds,
            )
            refresher.start()
            outcome = self._process_task(task)
            refresher.stop()
            refresher.join(timeout=1)
            if outcome == "processed":
                summary.processed_tasks += 1
            elif outcome == "lease_lost":
                summary.lost_leases += 1
            else:
                summary.failed_tasks += 1

        return summary

    def _process_task(self, task: Task) -> str:
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
            return "processed"

        except TaskLeaseLostError:
            logger.error(
                f"Worker {self.worker_id} stopped task {task.id} because "
                "its lease was lost"
            )
            return "lease_lost"

        except Exception as exc:  # pragma: no cover - the heavy pipeline is mocked in tests
            duration = time.time() - start_time
            logger.error(
                f"Worker {self.worker_id} failed to process task {task.id}: {exc}"
            )
            try:
                self.db.update_task_status(
                    task.id,
                    "Failed",
                    error_message=str(exc),
                    processing_duration=duration,
                )
            except TaskLeaseLostError:
                logger.error(
                    f"Worker {self.worker_id} could not fail task {task.id} "
                    "because its lease was lost"
                )
                return "lease_lost"
            return "failed"


def process_pending_tasks(
    *,
    db: TaskQueue,
    worker_id: Optional[str] = None,
    task_lock_timeout_seconds: int = TASK_LOCK_TIMEOUT_SECONDS,
    task_lease_heartbeat_seconds: int = TASK_LEASE_HEARTBEAT_SECONDS,
) -> ProcessingSummary:
    """Drain tasks from a lease-aware queue until no work remains."""
    worker = ProcessingWorker(
        db,
        worker_id=worker_id,
        task_lock_timeout_seconds=task_lock_timeout_seconds,
        task_lease_heartbeat_seconds=task_lease_heartbeat_seconds,
    )
    return worker.run()
