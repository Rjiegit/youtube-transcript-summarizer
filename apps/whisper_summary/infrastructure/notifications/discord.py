from __future__ import annotations

from typing import Any, Callable, Optional
from urllib.parse import urlsplit
from uuid import UUID

try:  # pragma: no cover - optional dependency
    import requests
    from requests import RequestException
except ModuleNotFoundError:  # pragma: no cover - testing scaffold
    requests = None  # type: ignore

    class RequestException(Exception):  # type: ignore
        pass

from whisper_summary.core.logger import logger

DEFAULT_TIMEOUT_SECONDS = 10
PostFunc = Callable[..., Any]


def send_task_completion_notification(
    title: str,
    youtube_url: str,
    webhook_url: Optional[str],
    *,
    notion_task_id: Optional[str] = None,
    showcase_base_url: Optional[str] = None,
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

    message_lines = [f"✅ 任務完成：{title}", youtube_url]

    notion_task_id_value = (notion_task_id or "").strip()
    showcase_base = (showcase_base_url or "").strip().rstrip("/")
    if showcase_base:
        try:
            parsed = urlsplit(showcase_base)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.query
                or parsed.fragment
                or any(character.isspace() for character in showcase_base)
            ):
                raise ValueError("Invalid showcase base URL")
            # Accessing port also validates malformed port values.
            parsed.port
            page_id = str(UUID(notion_task_id_value))
        except ValueError:
            logger.info("Invalid showcase URL or summary page ID; omitting knowledge link.")
        else:
            message_lines.append(f"知識庫：{showcase_base}/results/{page_id}")

    payload = {
        "content": "\n".join(message_lines),
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
