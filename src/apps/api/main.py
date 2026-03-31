"""FastAPI server exposing task management endpoints."""

from __future__ import annotations

import os
from datetime import datetime
from fastapi import FastAPI, Header, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.logger import logger
from src.core.time_utils import as_utc, utc_now
from src.core.utils.url import (
    build_youtube_channel_feed_url,
    is_valid_youtube_channel_id,
    is_valid_youtube_url,
    normalize_youtube_url,
)
from src.domain.interfaces.database import ProcessingLockInfo
from src.infrastructure.persistence.factory import DBFactory
from src.infrastructure.persistence.sqlite.rss_subscription_repository import (
    SQLiteRSSSubscriptionRepository,
)
from src.services.pipeline.processing_runner import PROCESSING_LOCK_TIMEOUT_SECONDS
from src.services.tasks.processing_scheduler import (
    SchedulingResult,
    schedule_processing_job,
)
from src.services.rss.subscription_service import create_rss_subscription
from src.services.tasks.task_creation import create_task_record

SUPPORTED_DB_TYPES = {"sqlite", "notion"}
REQUIRED_NOTION_ENV_VARS: tuple[str, ...] = ("NOTION_API_KEY", "NOTION_DATABASE_ID")
FAILED_RETRY_CREATED_STATUS = "Failed Retry Created"
TASK_CACHE_TTL_SECONDS: int = int(
    os.environ.get("TASK_CACHE_TTL_SECONDS", "3600")
)


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
    source_type: str = Field(
        default="manual",
        description="Origin of the task creation request (manual|rss).",
    )
    source_channel_id: str | None = Field(
        default=None,
        description="Optional source channel identifier when the task was created from RSS.",
    )
    completed_task_policy: str = Field(
        default="cache_ttl",
        description="Completed-task dedup policy (cache_ttl|block_existing).",
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

    @field_validator("source_type")
    @classmethod
    def normalize_source_type(cls, value: str) -> str:
        normalized = (value or "").lower()
        if normalized not in {"manual", "rss"}:
            raise ValueError("source_type must be either 'manual' or 'rss'.")
        return normalized

    @field_validator("completed_task_policy")
    @classmethod
    def normalize_completed_task_policy(cls, value: str) -> str:
        normalized = (value or "").lower()
        if normalized not in {"cache_ttl", "block_existing"}:
            raise ValueError(
                "completed_task_policy must be either 'cache_ttl' or 'block_existing'."
            )
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
    cached: bool = Field(
        default=False,
        description="True when the response was served from a recent completed task.",
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


class RSSSubscriptionCreateRequest(BaseModel):
    """Incoming payload for creating an RSS channel subscription."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    channel_id: str = Field(..., description="YouTube channel id.")
    feed_url: str | None = Field(
        default=None,
        description="Optional canonical YouTube feed URL for the channel.",
    )
    title: str | None = Field(
        default="",
        description="Optional display title for the subscription.",
    )
    enabled: bool = Field(
        default=True,
        description="Whether the subscription should be enabled immediately.",
    )

    @field_validator("channel_id")
    @classmethod
    def validate_channel_id(cls, value: str) -> str:
        if not is_valid_youtube_channel_id(value):
            raise ValueError("channel_id must be a valid YouTube channel id.")
        return value


class RSSSubscriptionCreateResponse(BaseModel):
    """Response payload after creating an RSS subscription."""

    subscription_id: str = Field(..., description="Identifier of the subscription.")
    channel_id: str = Field(..., description="YouTube channel id.")
    feed_url: str = Field(..., description="Canonical YouTube feed URL.")
    title: str = Field(..., description="Display title for the subscription.")
    enabled: bool = Field(..., description="Whether the subscription is enabled.")
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


def _get_rss_repository() -> SQLiteRSSSubscriptionRepository:
    db = DBFactory.get_db("sqlite")
    db_path = getattr(db, "db_path", "data/tasks.db")
    return SQLiteRSSSubscriptionRepository(db_path=db_path)


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
    now = utc_now()
    age_seconds: float | None = None
    locked_at = None
    if info.locked_at:
        locked_at = as_utc(info.locked_at)
        age_seconds = max(0.0, (now - locked_at).total_seconds())
    stale = (
        age_seconds is not None and age_seconds >= PROCESSING_LOCK_TIMEOUT_SECONDS
    )
    return ProcessingLockSnapshot(
        worker_id=info.worker_id,
        locked_at=locked_at,
        age_seconds=age_seconds,
        stale=stale,
    )

def _schedule_processing_job(
    *,
    db_type: str,
    db,
    worker_id: str | None = None,
) -> SchedulingResult:
    """Shared helper to schedule the background worker with locking semantics."""
    try:
        return schedule_processing_job(
            db_type=db_type,
            db=db,
            worker_id=worker_id,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@app.post("/tasks", response_model=TaskCreateResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreateRequest, response: Response):
    """Create a new task and persist it in the selected backend.

    Deduplication rules (based on normalised URL):
    * **Completed within TTL** → 200 with cached result.
    * **Pending / Processing** → 409 Conflict.
    * Otherwise → 201 new task.
    """

    normalized_url = normalize_youtube_url(payload.url)
    if not normalized_url or not is_valid_youtube_url(normalized_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid YouTube URL.",
        )

    _ensure_db_configuration(payload.db_type)
    db = _get_database(payload.db_type)

    try:
        creation = create_task_record(
            db=db,
            url=normalized_url,
            source_type=payload.source_type,
            source_channel_id=payload.source_channel_id,
            cache_ttl_seconds=TASK_CACHE_TTL_SECONDS,
            completed_task_policy=payload.completed_task_policy,
        )
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

    if creation.outcome in {"duplicate_active", "duplicate_completed"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=creation.message,
        )

    if creation.cached and creation.task is not None:
        response.status_code = status.HTTP_200_OK
        return TaskCreateResponse(
            task_id=str(creation.task.id),
            status=creation.task.status,
            db_type=payload.db_type,
            message=creation.message,
            processing_started=False,
            processing_worker_id=None,
            cached=True,
        )

    task = creation.task
    if task is None:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task creation returned no task.",
        )

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

    message = creation.message
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
        cached=False,
    )


@app.post(
    "/rss/subscriptions",
    response_model=RSSSubscriptionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rss_subscription_endpoint(
    payload: RSSSubscriptionCreateRequest,
) -> RSSSubscriptionCreateResponse:
    """Create a YouTube RSS channel subscription in SQLite."""

    repository = _get_rss_repository()
    feed_url = payload.feed_url or build_youtube_channel_feed_url(payload.channel_id)
    try:
        result = create_rss_subscription(
            repository,
            channel_id=payload.channel_id,
            feed_url=feed_url,
            title=payload.title or "",
            enabled=payload.enabled,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_409_CONFLICT if "已存在" in detail else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create RSS subscription.",
        ) from exc

    return RSSSubscriptionCreateResponse(
        subscription_id=result.subscription_id or "",
        channel_id=result.channel_id,
        feed_url=result.feed_url,
        title=result.title,
        enabled=result.enabled,
        message=result.message,
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
