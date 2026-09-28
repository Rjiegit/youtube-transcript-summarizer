from __future__ import annotations

from typing import Protocol

from whisper_summary.domain.tasks.models import Task


class TaskQueue(Protocol):
    """Minimal lease-aware queue contract required by a processing worker."""

    def acquire_next_task(
        self,
        worker_id: str,
        lock_timeout_seconds: int = 300,
    ) -> Task | None: ...

    def refresh_task_lease(
        self,
        task_id: str,
        worker_id: str,
        lease_token: str,
    ) -> bool: ...

    def update_task_status(
        self,
        task_id: str,
        status: str,
        title: str | None = None,
        summary: str | None = None,
        error_message: str | None = None,
        processing_duration: float | None = None,
        notion_page_id: str | None = None,
        processing_engine: str | None = None,
    ) -> bool | None: ...
