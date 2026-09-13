"""Shared FastAPI dependencies and infrastructure factories."""

import os

from fastapi import HTTPException, status

from whisper_summary.domain.ports.repositories import RSSSubscriptionRepository
from whisper_summary.infrastructure.repository_composition import create_database, create_rss_repository
from whisper_summary.services.tasks.processing_scheduler import SchedulingResult

# Compatibility patch seam for older callers; API execution no longer invokes it.
schedule_processing_job = None

REQUIRED_NOTION_ENV_VARS: tuple[str, ...] = ("NOTION_API_KEY", "NOTION_DATABASE_ID")


def ensure_db_configuration(db_type: str) -> None:
    if db_type == "notion":
        missing = [var for var in REQUIRED_NOTION_ENV_VARS if not os.environ.get(var)]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing Notion configuration: {', '.join(missing)}",
            )


def get_database(db_type: str):
    try:
        return create_database(db_type)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


def get_rss_repository() -> RSSSubscriptionRepository:
    db = create_database("sqlite")
    db_path = getattr(db, "db_path", "data/tasks.db")
    return create_rss_repository(db_path=db_path)


def schedule_job(*, db_type: str, db, worker_id: str | None = None) -> SchedulingResult:
    """Report dedicated-worker mode without spawning work in the API process."""
    return SchedulingResult(
        accepted=False,
        worker_id=None,
        message="Task queued for the dedicated processing worker.",
    )
