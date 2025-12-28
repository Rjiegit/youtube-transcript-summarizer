from __future__ import annotations

import os
from typing import Any, Dict

from src.apps.ui.ui_config import API_BASE_URL
from src.apps.ui.ui_runtime import require_requests, requests


def get_processing_lock_admin_token() -> str | None:
    token = os.environ.get("PROCESSING_LOCK_ADMIN_TOKEN")
    if token:
        return token.strip()
    return None


def call_create_task_api(payload: Dict[str, Any]) -> tuple[int, Dict[str, Any]]:
    """Send POST to /tasks and return status + payload."""
    require_requests()
    endpoint = f"{API_BASE_URL.rstrip('/')}/tasks"
    response = requests.post(endpoint, json=payload, timeout=10)
    try:
        body: Dict[str, Any] = response.json()
    except ValueError:
        body = {}
    return response.status_code, body


def call_processing_api(payload: Dict[str, Any]) -> tuple[int, Dict[str, Any]]:
    """Send POST to /processing-jobs and return status + payload."""
    require_requests()
    endpoint = f"{API_BASE_URL.rstrip('/')}/processing-jobs"
    response = requests.post(endpoint, json=payload, timeout=10)
    try:
        body: Dict[str, Any] = response.json()
    except ValueError:
        body = {}
    return response.status_code, body


def call_retry_task_api(
    task_id: str, payload: Dict[str, Any]
) -> tuple[int, Dict[str, Any]]:
    """Send POST to /tasks/{task_id}/retry and return status + payload."""
    require_requests()
    endpoint = f"{API_BASE_URL.rstrip('/')}/tasks/{task_id}/retry"
    response = requests.post(endpoint, json=payload, timeout=10)
    try:
        body: Dict[str, Any] = response.json()
    except ValueError:
        body = {}
    return response.status_code, body


def call_processing_lock_status(
    db_choice: str, maintainer_token: str | None = None
) -> tuple[int, Dict[str, Any]]:
    require_requests()
    endpoint = f"{API_BASE_URL.rstrip('/')}/processing-lock"
    token = maintainer_token or get_processing_lock_admin_token()
    headers = {"X-Maintainer-Token": token} if token else {}
    params = {"db_type": db_choice.lower()}

    response = requests.get(endpoint, headers=headers, params=params, timeout=10)
    try:
        body: Dict[str, Any] = response.json()
    except ValueError:
        body = {}
    return response.status_code, body


def call_processing_lock_release(
    db_choice: str,
    payload: Dict[str, Any],
    maintainer_token: str | None = None,
) -> tuple[int, Dict[str, Any]]:
    require_requests()
    endpoint = f"{API_BASE_URL.rstrip('/')}/processing-lock"
    token = maintainer_token or get_processing_lock_admin_token()
    headers = {"X-Maintainer-Token": token} if token else {}
    body_payload = {"db_type": db_choice.lower(), **payload}
    response = requests.delete(
        endpoint,
        headers=headers,
        json=body_payload,
        timeout=10,
    )
    try:
        body: Dict[str, Any] = response.json()
    except ValueError:
        body = {}
    return response.status_code, body
