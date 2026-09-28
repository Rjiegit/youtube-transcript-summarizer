from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def sort_tasks_for_display(tasks: list[Any]) -> list[Any]:
    """Sort tasks by created_at desc, falling back to id ordering."""

    def _sort_key(task: Any):
        created = getattr(task, "created_at", None)
        if created is None or not isinstance(created, datetime):
            return datetime.min.replace(tzinfo=timezone.utc)
        return created

    return sorted(tasks, key=_sort_key, reverse=True)


ALLOWED_STATUS_OPTIONS = [
    "Pending",
    "Processing",
    "Completed",
    "Failed",
    "Failed Retry Created",
]


def collect_task_status_options(tasks: list[Any]) -> list[str]:
    """Return fixed status filter options."""
    return list(ALLOWED_STATUS_OPTIONS)


def filter_tasks_by_status(tasks: list[Any], selected_statuses: list[str] | None) -> list[Any]:
    """Filter tasks by selected statuses; None means no filtering."""
    if selected_statuses is None:
        return tasks
    if not selected_statuses:
        return []
    selected_set = set(selected_statuses)
    return [task for task in tasks if getattr(task, "status", None) in selected_set]
