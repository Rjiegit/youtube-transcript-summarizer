"""FastAPI server exposing task management endpoints."""

from __future__ import annotations

import os
import threading
import uuid
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.logger import logger
from src.core.utils.url import normalize_youtube_url, is_valid_youtube_url
from src.domain.interfaces.database import ProcessingLockInfo
from src.infrastructure.persistence.factory import DBFactory
from src.services.pipeline.processing_runner import (
    PROCESSING_LOCK_TIMEOUT_SECONDS,
    process_pending_tasks,
)

SUPPORTED_DB_TYPES = {"sqlite", "notion"}
REQUIRED_NOTION_ENV_VARS: tuple[str, ...] = ("NOTION_API_KEY", "NOTION_DATABASE_ID")
FAILED_RETRY_CREATED_STATUS = "Failed Retry Created"


def _normalize_db_type(value: str) -> str:
    normalized = (value or "").lower()
    if normalized not in SUPPORTED_DB_TYPES:
        raise ValueError("db_type must be either 'sqlite' or 'notion'.")
    return normalized


class TaskCreateRequest(BaseModel):
    """Incoming payload for creating a new task."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    url: str = Field(..., description="YouTube URL to add to the processing queue.")
    db_type: str = Field(
        default="sqlite",
        description="Database backend to persist the task (sqlite|notion).",
    )

    @field_validator("url")
    @classmethod
    def validate_url_presence(cls, value: str) -> str:
        if not value:
            raise ValueError("URL is required.")
        return value

    @field_validator("db_type")
    @classmethod
    def normalize_db_type(cls, value: str) -> str:
        normalized = (value or "").lower()
        if normalized not in SUPPORTED_DB_TYPES:
            raise ValueError("db_type must be either 'sqlite' or 'notion'.")
        return normalized


class TaskCreateResponse(BaseModel):
    """Standard response after creating a task."""

    task_id: str = Field(..., description="Identifier of the queued task.")
    status: str = Field(..., description="Current status of the task.")
    db_type: str = Field(..., description="Database backend used to persist the task.")
    message: str = Field(..., description="Human readable status message.")
    processing_started: bool = Field(
        default=False,
        description="Indicates whether a background worker was scheduled.",
    )
    processing_worker_id: str | None = Field(
        default=None,
        description="Worker identifier if background processing was scheduled.",
    )


class TaskRetryRequest(BaseModel):
    """Incoming payload for retrying a failed task."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    db_type: str = Field(
        default="sqlite",
        description="Database backend to persist the retry task (sqlite|notion).",
    )
    retry_reason: str | None = Field(
        default=None,
        description="Optional reason for retrying the task.",
    )

    @field_validator("db_type")
    @classmethod
    def normalize_db_type(cls, value: str) -> str:
        normalized = (value or "").lower()
        if normalized not in SUPPORTED_DB_TYPES:
            raise ValueError("db_type must be either 'sqlite' or 'notion'.")
        return normalized


class TaskRetryResponse(BaseModel):
    """Standard response after creating a retry task."""

    task_id: str = Field(..., description="Identifier of the newly created retry task.")
    source_task_id: str = Field(..., description="Identifier of the failed task being retried.")
    status: str = Field(..., description="Current status of the retry task.")
    db_type: str = Field(..., description="Database backend used to persist the retry task.")
    message: str = Field(..., description="Human readable status message.")


class ProcessingJobCreateRequest(BaseModel):
    """Incoming payload for triggering the processing worker."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    db_type: str = Field(
        default="sqlite",
        description="Database backend to drain tasks from (sqlite|notion).",
    )
    worker_id: str | None = Field(
        default=None,
        description="Optional human-readable worker identifier.",
    )

    @field_validator("db_type")
    @classmethod
    def normalize_db_type(cls, value: str) -> str:
        normalized = (value or "").lower()
        if normalized not in SUPPORTED_DB_TYPES:
            raise ValueError("db_type must be either 'sqlite' or 'notion'.")
        return normalized


class ProcessingJobCreateResponse(BaseModel):
    """Response payload after scheduling a processing job."""

    worker_id: str = Field(..., description="Identifier assigned to the worker run.")
    db_type: str = Field(..., description="Database backend being processed.")
    accepted: bool = Field(..., description="Indicates whether the run was scheduled.")
    message: str = Field(..., description="Human readable status message.")


class ProcessingLockSnapshot(BaseModel):
    """Representation of the processing lock state for inspection."""

    model_config = ConfigDict(extra="forbid")

    worker_id: str | None = Field(
        default=None,
        description="Identifier of the worker holding the lock.",
    )
    locked_at: datetime | None = Field(
        default=None,
        description="UTC timestamp of when the lock was last refreshed.",
    )
    age_seconds: float | None = Field(
        default=None,
        description="Seconds since the lock was last refreshed.",
    )
    stale: bool = Field(
        default=False,
        description="Indicates whether the lock has exceeded the timeout threshold.",
    )


class ProcessingLockStatusResponse(BaseModel):
    """Response payload for GET /processing-lock."""

    model_config = ConfigDict(extra="forbid")

    db_type: str = Field(..., description="Database backend being inspected.")
    snapshot: ProcessingLockSnapshot = Field(
        ...,
        description="Snapshot of the current processing lock.",
    )


class ProcessingLockReleaseRequest(BaseModel):
    """Incoming payload when attempting to release the processing lock."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    db_type: str = Field(
        default="sqlite",
        description="Database backend whose lock is being inspected (sqlite|notion).",
    )
    expected_worker_id: str | None = Field(
        default=None,
        description="Worker ID that must match the current lock holder (unless force=true).",
    )
    force: bool = Field(
        default=False,
        description="Whether to forcibly clear the lock even if the expected worker does not match.",
    )
    force_threshold_seconds: int | None = Field(
        default=None,
        description="Minimum age (in seconds) the lock must reach before a forced clear is allowed.",
    )
    reason: str | None = Field(
        default=None,
        description="Human-readable note describing why the lock is being released.",
    )
    dry_run: bool = Field(
        default=False,
        description="If true, the API only reports the current lock state without modifying it.",
    )

    @field_validator("db_type")
    @classmethod
    def _normalize_db_type(cls, value: str) -> str:
        return _normalize_db_type(value)

    @field_validator("force_threshold_seconds")
    @classmethod
    def _validate_threshold(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 0:
            raise ValueError("force_threshold_seconds must be greater than or equal to 0.")
        return value


class ProcessingLockReleaseResponse(BaseModel):
    """Response payload after attempting to release the lock."""

    model_config = ConfigDict(extra="forbid")

    db_type: str = Field(..., description="Database backend that was inspected.")
    released: bool = Field(
        ...,
        description="True if the lock was cleared; false if it remained untouched.",
    )
    reason: str | None = Field(
        default=None,
        description="Optional explanation for why the lock was or was not released.",
    )
    before: ProcessingLockSnapshot = Field(
        ...,
        description="Lock snapshot observed before any action.",
    )
    after: ProcessingLockSnapshot = Field(
        ...,
        description="Lock snapshot after taking the requested action.",
    )


app = FastAPI(
    title="Task API",
    version="1.0.0",
    description="HTTP endpoints for managing transcription tasks.",
)


def _ensure_db_configuration(db_type: str) -> None:
    if db_type == "notion":
        missing = [var for var in REQUIRED_NOTION_ENV_VARS if not os.environ.get(var)]
        if missing:
            missing_str = ", ".join(missing)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing Notion configuration: {missing_str}",
            )


def _get_database(db_type: str):
    try:
        return DBFactory.get_db(db_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


def _ensure_maintainer_token(token: str | None) -> None:
    admin_token = os.environ.get("PROCESSING_LOCK_ADMIN_TOKEN")
    if not admin_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Processing lock admin token is not configured.",
        )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing maintainer token.",
        )
    if token != admin_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid maintainer token.",
        )


def _build_lock_snapshot(info: ProcessingLockInfo) -> ProcessingLockSnapshot:
    now = datetime.utcnow()
    age_seconds: float | None = None
    if info.locked_at:
        age_seconds = max(0.0, (now - info.locked_at).total_seconds())
    stale = (
        age_seconds is not None and age_seconds >= PROCESSING_LOCK_TIMEOUT_SECONDS
    )
    return ProcessingLockSnapshot(
        worker_id=info.worker_id,
        locked_at=info.locked_at,
        age_seconds=age_seconds,
        stale=stale,
    )


def _run_processing_worker(db_type: str, worker_id: str) -> None:
    """Background task that drains the queue and guarantees lock release."""
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


@dataclass
class SchedulingResult:
    accepted: bool
    worker_id: str | None
    message: str


def _schedule_processing_job(
    *,
    db_type: str,
    db,
    worker_id: str | None = None,
) -> SchedulingResult:
    """Shared helper to schedule the background worker with locking semantics."""

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule processing worker.",
        ) from exc

    logger.info(
        f"Scheduled processing worker {assigned_worker_id} for backend {db_type}"
    )

    return SchedulingResult(
        accepted=True,
        worker_id=assigned_worker_id,
        message="Processing worker scheduled.",
    )


@app.post("/tasks", response_model=TaskCreateResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreateRequest) -> TaskCreateResponse:
    """Create a new task and persist it in the selected backend."""

    normalized_url = normalize_youtube_url(payload.url)
    if not normalized_url or not is_valid_youtube_url(normalized_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid YouTube URL.",
        )

    _ensure_db_configuration(payload.db_type)
    db = _get_database(payload.db_type)

    try:
        task = db.add_task(normalized_url)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task.",
        ) from exc

    try:
        scheduling_result = _schedule_processing_job(
            db_type=payload.db_type,
            db=db,
        )
    except HTTPException as exc:
        logger.error(
            f"Failed to schedule processing worker after task creation: {exc.detail}"
        )
        scheduling_result = SchedulingResult(
            accepted=False,
            worker_id=None,
            message=str(exc.detail) if exc.detail else "Failed to schedule processing worker.",
        )
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.error(
            f"Failed to schedule processing worker after task creation: {exc}"
        )
        scheduling_result = SchedulingResult(
            accepted=False,
            worker_id=None,
            message="Task queued, but failed to schedule processing worker.",
        )

    message = "Task queued successfully."
    if scheduling_result.accepted:
        worker_note = (
            f" Processing worker scheduled (worker: {scheduling_result.worker_id})."
        )
        message += worker_note
    else:
        message += f" {scheduling_result.message}"

    return TaskCreateResponse(
        task_id=str(task.id),
        status=task.status,
        db_type=payload.db_type,
        message=message,
        processing_started=scheduling_result.accepted,
        processing_worker_id=scheduling_result.worker_id,
    )


@app.post(
    "/tasks/{task_id}/retry",
    response_model=TaskRetryResponse,
    status_code=status.HTTP_201_CREATED,
)
def retry_task(task_id: str, payload: TaskRetryRequest) -> TaskRetryResponse:
    """Create a retry task from a failed task."""

    _ensure_db_configuration(payload.db_type)
    db = _get_database(payload.db_type)

    source_task = db.get_task_by_id(task_id)
    if not source_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    if source_task.status != "Failed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task status must be Failed to retry.",
        )

    try:
        new_task = db.create_retry_task(source_task, payload.retry_reason)
        db.update_task_status(source_task.id, FAILED_RETRY_CREATED_STATUS)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create retry task.",
        ) from exc

    return TaskRetryResponse(
        task_id=str(new_task.id),
        source_task_id=str(source_task.id),
        status=new_task.status,
        db_type=payload.db_type,
        message="Retry task created.",
    )


@app.post(
    "/processing-jobs",
    response_model=ProcessingJobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_processing_job_endpoint(
    payload: ProcessingJobCreateRequest,
) -> ProcessingJobCreateResponse:
    """Schedule the background worker that drains the task queue."""

    _ensure_db_configuration(payload.db_type)
    db = _get_database(payload.db_type)

    scheduling_result = _schedule_processing_job(
        db_type=payload.db_type,
        db=db,
        worker_id=payload.worker_id,
    )

    if not scheduling_result.accepted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=scheduling_result.message,
        )

    return ProcessingJobCreateResponse(
        worker_id=scheduling_result.worker_id or "",
        db_type=payload.db_type,
        accepted=True,
        message=scheduling_result.message,
    )


@app.get(
    "/processing-lock",
    response_model=ProcessingLockStatusResponse,
    status_code=status.HTTP_200_OK,
)
def get_processing_lock_status(
    db_type: str = "sqlite",
    maintainer_token: str | None = Header(None, alias="X-Maintainer-Token"),
) -> ProcessingLockStatusResponse:
    """Inspect the current processing lock for the selected backend."""

    normalized_db_type = _normalize_db_type(db_type)
    _ensure_maintainer_token(maintainer_token)
    _ensure_db_configuration(normalized_db_type)
    db = _get_database(normalized_db_type)
    snapshot = _build_lock_snapshot(db.read_processing_lock())
    logger.info(
        f"Maintainer inspected processing lock for {normalized_db_type} "
        f"(worker={snapshot.worker_id}, stale={snapshot.stale})"
    )
    return ProcessingLockStatusResponse(
        db_type=normalized_db_type,
        snapshot=snapshot,
    )


@app.delete(
    "/processing-lock",
    response_model=ProcessingLockReleaseResponse,
    status_code=status.HTTP_200_OK,
)
def delete_processing_lock(
    payload: ProcessingLockReleaseRequest,
    maintainer_token: str | None = Header(None, alias="X-Maintainer-Token"),
) -> ProcessingLockReleaseResponse:
    """Attempt to release the global processing lock, optionally forcing it."""

    _ensure_maintainer_token(maintainer_token)
    _ensure_db_configuration(payload.db_type)
    db = _get_database(payload.db_type)
    before_info = db.read_processing_lock()
    before_snapshot = _build_lock_snapshot(before_info)

    if not before_info.worker_id:
        logger.info(
            f"Processing lock release requested for {payload.db_type} "
            "but no lock was present."
        )
        return ProcessingLockReleaseResponse(
            db_type=payload.db_type,
            released=False,
            reason="lock_not_found",
            before=before_snapshot,
            after=before_snapshot,
        )

    if payload.dry_run:
        logger.info(
            f"Processing lock dry-run for {payload.db_type} (worker={before_info.worker_id})."
        )
        return ProcessingLockReleaseResponse(
            db_type=payload.db_type,
            released=False,
            reason=payload.reason or "dry_run",
            before=before_snapshot,
            after=before_snapshot,
        )

    if payload.force:
        threshold = payload.force_threshold_seconds or 0
        lock_age = before_snapshot.age_seconds or 0.0
        if threshold > 0 and lock_age < threshold:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Processing lock has not aged enough for a forced release.",
            )

        db.clear_processing_lock()
        after_snapshot = _build_lock_snapshot(db.read_processing_lock())
        logger.info(
            f"Processing lock force-released for {payload.db_type} "
            f"(worker={before_info.worker_id}, reason={payload.reason})"
        )
        return ProcessingLockReleaseResponse(
            db_type=payload.db_type,
            released=True,
            reason=payload.reason,
            before=before_snapshot,
            after=after_snapshot,
        )

    if not payload.expected_worker_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="expected_worker_id is required unless force=true.",
        )

    if before_info.worker_id != payload.expected_worker_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lock is held by {before_info.worker_id}.",
        )

    db.release_processing_lock(before_info.worker_id)
    after_snapshot = _build_lock_snapshot(db.read_processing_lock())
    logger.info(
        f"Processing lock released for {payload.db_type} (worker={before_info.worker_id})."
    )
    return ProcessingLockReleaseResponse(
        db_type=payload.db_type,
        released=True,
        reason=payload.reason,
        before=before_snapshot,
        after=after_snapshot,
    )
