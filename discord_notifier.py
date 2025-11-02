from __future__ import annotations

from typing import Any, Callable, Optional

try:  # pragma: no cover - optional dependency
    import requests
    from requests import RequestException
except ModuleNotFoundError:  # pragma: no cover - testing scaffold
    requests = None  # type: ignore

    class RequestException(Exception):  # type: ignore
        pass

from logger import logger

DEFAULT_TIMEOUT_SECONDS = 10
PostFunc = Callable[..., Any]


def send_task_completion_notification(
    title: str,
    youtube_url: str,
    webhook_url: Optional[str],
    *,
    post: Optional[PostFunc] = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> bool:
    """
    Send a task completion notification to Discord.

    Returns True when the webhook reports success, False otherwise.
    """
    if not webhook_url:
        logger.info("Discord webhook not configured; skipping notification.")
        return False

    sender = post
    if sender is None:
        if requests is None:
            logger.warning("requests package missing; cannot send Discord notification.")
            return False
        sender = requests.post

    payload = {
        "content": f"✅ 任務完成：{title}\n{youtube_url}",
    }

    try:
        response = sender(webhook_url, json=payload, timeout=timeout_seconds)
    except RequestException as exc:  # pragma: no cover - network failure path
        logger.warning(f"Failed to send Discord notification: {exc}")
        return False

    status_code = getattr(response, "status_code", None)
    if status_code is not None and status_code >= 400:
        body = getattr(response, "text", "")
        logger.warning(f"Discord webhook returned {status_code}: {body}")
        return False

    logger.info("Discord notification delivered.")
    return True
