"""FastAPI server exposing task management endpoints."""

from __future__ import annotations

import os
import uuid
from contextlib import suppress

from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.db_factory import DBFactory
from logger import logger
from processing import (
    PROCESSING_LOCK_TIMEOUT_SECONDS,
    process_pending_tasks,
)
from url_validator import normalize_youtube_url, is_valid_youtube_url

SUPPORTED_DB_TYPES = {"sqlite", "notion"}
REQUIRED_NOTION_ENV_VARS: tuple[str, ...] = ("NOTION_API_KEY", "NOTION_DATABASE_ID")


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

    return TaskCreateResponse(
        task_id=str(task.id),
        status=task.status,
        db_type=payload.db_type,
        message="Task queued successfully.",
    )


@app.post(
    "/processing-jobs",
    response_model=ProcessingJobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_processing_job_endpoint(
    payload: ProcessingJobCreateRequest, background_tasks: BackgroundTasks
) -> ProcessingJobCreateResponse:
    """Schedule the background worker that drains the task queue."""

    _ensure_db_configuration(payload.db_type)
    db = _get_database(payload.db_type)

    worker_id = payload.worker_id or f"api-worker-{uuid.uuid4().hex}"

    try:
        lock_acquired = db.acquire_processing_lock(
            worker_id,
            PROCESSING_LOCK_TIMEOUT_SECONDS,
        )
    except NotImplementedError:  # pragma: no cover - for non-locking backends
        lock_acquired = True

    if not lock_acquired:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Processing already running.",
        )

    try:
        background_tasks.add_task(_run_processing_worker, payload.db_type, worker_id)
    except Exception as exc:  # pragma: no cover - defensive guard
        with suppress(Exception):
            db.release_processing_lock(worker_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule processing worker.",
        ) from exc

    logger.info(
        f"Scheduled processing worker {worker_id} for backend {payload.db_type}"
    )

    return ProcessingJobCreateResponse(
        worker_id=worker_id,
        db_type=payload.db_type,
        accepted=True,
        message="Processing worker scheduled.",
    )
