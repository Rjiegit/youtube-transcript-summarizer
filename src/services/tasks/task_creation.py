from __future__ import annotations

from dataclasses import dataclass

from src.core.time_utils import as_utc, utc_now
from src.domain.interfaces.database import BaseDB
from src.domain.tasks.models import Task


@dataclass
class TaskCreationResult:
    outcome: str
    task: Task | None
    message: str
    cached: bool = False

    @property
    def created(self) -> bool:
        return self.outcome == "created"


def create_task_record(
    *,
    db: BaseDB,
    url: str,
    source_type: str = "manual",
    source_channel_id: str | None = None,
    cache_ttl_seconds: int = 3600,
    completed_task_policy: str = "cache_ttl",
) -> TaskCreationResult:
    existing_task = db.find_recent_task_by_url(url)
    if existing_task is not None:
        if existing_task.status in ("Pending", "Processing"):
            return TaskCreationResult(
                outcome="duplicate_active",
                task=existing_task,
                message=(
                    f"A task for this URL is already {existing_task.status.lower()} "
                    f"(task_id={existing_task.id})."
                ),
            )

        if existing_task.status == "Completed":
            if completed_task_policy == "block_existing":
                return TaskCreationResult(
                    outcome="duplicate_completed",
                    task=existing_task,
                    message=f"A completed task already exists for this URL (task_id={existing_task.id}).",
                )
            if existing_task.created_at:
                age_seconds = (utc_now() - as_utc(existing_task.created_at)).total_seconds()
                if age_seconds < cache_ttl_seconds:
                    return TaskCreationResult(
                        outcome="cached_completed",
                        task=existing_task,
                        message=(
                            f"Returning cached result (age={int(age_seconds)}s, "
                            f"ttl={cache_ttl_seconds}s)."
                        ),
                        cached=True,
                    )

    task = db.add_task(
        url,
        source_type=source_type,
        source_channel_id=source_channel_id,
    )
    return TaskCreationResult(
        outcome="created",
        task=task,
        message="Task queued successfully.",
    )
