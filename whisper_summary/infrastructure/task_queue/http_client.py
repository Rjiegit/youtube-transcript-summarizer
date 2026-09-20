from __future__ import annotations

from typing import Any

import requests

from whisper_summary.domain.tasks.models import Task
from whisper_summary.domain.tasks.leases import TaskLeaseLostError


class TaskQueueError(RuntimeError):
    """Raised when the central task queue cannot complete an operation."""


class HttpTaskQueue:
    """Lease-aware HTTP adapter for the central task queue API."""

    def __init__(
        self,
        base_url: str,
        worker_token: str,
        *,
        session=None,
        timeout_seconds: float = 30.0,
    ):
        if not worker_token.strip():
            raise ValueError("PROCESSING_WORKER_TOKEN is required")
        self.base_url = base_url.rstrip("/")
        self.worker_token = worker_token
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds
        self._leases: dict[str, tuple[str, str]] = {}

    @property
    def _headers(self) -> dict[str, str]:
        return {"X-Worker-Token": self.worker_token}

    def _check_response(self, response) -> None:
        if response.status_code == 409:
            raise TaskLeaseLostError("Task lease is no longer owned by this worker")
        if response.status_code >= 400:
            detail = (getattr(response, "text", "") or "")[:500]
            raise TaskQueueError(
                f"Task queue returned HTTP {response.status_code}: {detail}"
            )

    def _lease_payload(self, task_id: str) -> dict[str, str]:
        lease = self._leases.get(str(task_id))
        if lease is None:
            raise TaskLeaseLostError(f"No lease is registered for task {task_id}")
        worker_id, lease_token = lease
        return {"worker_id": worker_id, "lease_token": lease_token}

    def acquire_next_task(
        self,
        worker_id: str,
        lock_timeout_seconds: int = 300,
    ) -> Task | None:
        del lock_timeout_seconds  # The API owns the lease timeout policy.
        response = self.session.post(
            f"{self.base_url}/worker-tasks/claim",
            headers=self._headers,
            json={"worker_id": worker_id},
            timeout=self.timeout_seconds,
        )
        if response.status_code == 204:
            return None
        self._check_response(response)
        payload = response.json()
        task_data = payload["task"]
        lease_token = payload["lease_token"]
        task = Task(
            id=str(task_data["id"]),
            url=task_data["url"],
            status=task_data["status"],
            title=task_data.get("title") or "",
            notion_page_id=task_data.get("notion_page_id"),
            processing_engine=task_data.get("processing_engine"),
            worker_id=worker_id,
            lease_token=lease_token,
        )
        self._leases[task.id] = (worker_id, lease_token)
        return task

    def refresh_task_lease(
        self,
        task_id: str,
        worker_id: str,
        lease_token: str,
    ) -> bool:
        response = self.session.post(
            f"{self.base_url}/worker-tasks/{task_id}/heartbeat",
            headers=self._headers,
            json={"worker_id": worker_id, "lease_token": lease_token},
            timeout=self.timeout_seconds,
        )
        self._check_response(response)
        return response.status_code == 204

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
    ) -> bool:
        lease_payload: dict[str, Any] = self._lease_payload(task_id)
        if status == "Processing":
            method = self.session.patch
            endpoint = f"{self.base_url}/worker-tasks/{task_id}/progress"
            lease_payload.update(
                title=title,
                processing_engine=processing_engine,
            )
        elif status == "Completed":
            method = self.session.post
            endpoint = f"{self.base_url}/worker-tasks/{task_id}/complete"
            lease_payload.update(
                title=title or "",
                summary=summary or "",
                processing_duration=processing_duration or 0.0,
                notion_page_id=notion_page_id,
                processing_engine=processing_engine,
            )
        elif status == "Failed":
            method = self.session.post
            endpoint = f"{self.base_url}/worker-tasks/{task_id}/fail"
            lease_payload.update(
                error_message=error_message or "Worker processing failed",
                processing_duration=processing_duration or 0.0,
            )
        else:
            raise ValueError(f"Unsupported worker task status: {status}")

        response = method(
            endpoint,
            headers=self._headers,
            json=lease_payload,
            timeout=self.timeout_seconds,
        )
        self._check_response(response)
        return response.status_code == 204
