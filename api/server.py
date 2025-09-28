"""FastAPI server exposing task management endpoints."""

from __future__ import annotations

import os
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from database.db_factory import DBFactory
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
