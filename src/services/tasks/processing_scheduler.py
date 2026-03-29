from __future__ import annotations

import threading
import uuid
from contextlib import suppress
from dataclasses import dataclass

from src.core.logger import logger
from src.infrastructure.persistence.factory import DBFactory
from src.services.pipeline.processing_runner import (
    PROCESSING_LOCK_TIMEOUT_SECONDS,
    process_pending_tasks,
)


@dataclass
class SchedulingResult:
    accepted: bool
    worker_id: str | None
    message: str


def _run_processing_worker(db_type: str, worker_id: str) -> None:
    db = DBFactory.get_db(db_type)
    try:
        result = process_pending_tasks(db=db, worker_id=worker_id)
        logger.info(
            f"Processing worker {result.worker_id} finished (processed={result.processed_tasks}, failed={result.failed_tasks})"
        )
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.error(
            f"Processing worker {worker_id} crashed for database {db_type}: {exc}"
        )
    finally:
        with suppress(Exception):
            db.release_processing_lock(worker_id)


def schedule_processing_job(*, db_type: str, db, worker_id: str | None = None) -> SchedulingResult:
    assigned_worker_id = worker_id or f"api-worker-{uuid.uuid4().hex}"

    try:
        lock_acquired = db.acquire_processing_lock(
            assigned_worker_id, PROCESSING_LOCK_TIMEOUT_SECONDS
        )
    except NotImplementedError:  # pragma: no cover - for non-locking backends
        lock_acquired = True

    if not lock_acquired:
        return SchedulingResult(
            accepted=False,
            worker_id=None,
            message="Processing already running.",
        )

    try:
        worker_thread = threading.Thread(
            target=_run_processing_worker,
            args=(db_type, assigned_worker_id),
            daemon=True,
        )
        worker_thread.start()
    except Exception as exc:  # pragma: no cover - defensive guard
        with suppress(Exception):
            db.release_processing_lock(assigned_worker_id)
        raise RuntimeError("Failed to schedule processing worker.") from exc

    logger.info(
        f"Scheduled processing worker {assigned_worker_id} for backend {db_type}"
    )
    return SchedulingResult(
        accepted=True,
        worker_id=assigned_worker_id,
        message="Processing worker scheduled.",
    )
