"""Shared FastAPI dependencies and infrastructure factories."""

import os

from fastapi import HTTPException, status

from src.domain.ports.repositories import RSSSubscriptionRepository
from src.infrastructure.repository_composition import create_database, create_rss_repository
from src.services.tasks.processing_scheduler import SchedulingResult, schedule_processing_job

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
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


def get_rss_repository() -> RSSSubscriptionRepository:
    db = create_database("sqlite")
    db_path = getattr(db, "db_path", "data/tasks.db")
    return create_rss_repository(db_path=db_path)


def schedule_job(*, db_type: str, db, worker_id: str | None = None) -> SchedulingResult:
    try:
        return schedule_processing_job(db_type=db_type, db=db, worker_id=worker_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
