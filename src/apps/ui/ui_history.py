from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from src.apps.ui.ui_config import (
    RECENT_TASK_HISTORY_KEY,
    RECENT_TASK_HISTORY_STORE_PATH,
    RECENT_TASK_HISTORY_TTL_DAYS,
)
from src.apps.ui.ui_notion import get_notion_display
from src.apps.ui.ui_runtime import require_streamlit, st


def prune_recent_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cutoff = datetime.utcnow() - timedelta(days=RECENT_TASK_HISTORY_TTL_DAYS)
    pruned: list[dict[str, Any]] = []
    for entry in history:
        viewed_at = entry.get("viewed_at")
        if not viewed_at:
            continue
        try:
            viewed_time = datetime.fromisoformat(viewed_at)
        except (TypeError, ValueError):
            continue
        if viewed_time >= cutoff:
            pruned.append(entry)
    return pruned


def get_history_client_id() -> str:
    require_streamlit()
    params = dict(st.query_params)
    client_id_value = params.get("client_id")
    if isinstance(client_id_value, list):
        client_id = client_id_value[0] if client_id_value else ""
    else:
        client_id = client_id_value or ""
    if client_id:
        return client_id
    new_id = str(uuid.uuid4())
    st.query_params["client_id"] = new_id
    return new_id


def load_recent_history_store() -> dict[str, list[dict[str, Any]]]:
    if not RECENT_TASK_HISTORY_STORE_PATH.exists():
        return {}
    try:
        raw = RECENT_TASK_HISTORY_STORE_PATH.read_text(encoding="utf-8")
        parsed = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(parsed, dict):
        return {}
    store: dict[str, list[dict[str, Any]]] = {}
    for key, value in parsed.items():
        if isinstance(value, list):
            store[str(key)] = value
    return store


def save_recent_history_store(store: dict[str, list[dict[str, Any]]]) -> None:
    RECENT_TASK_HISTORY_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECENT_TASK_HISTORY_STORE_PATH.write_text(
        json.dumps(store, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def load_persistent_history() -> list[dict[str, Any]]:
    client_id = get_history_client_id()
    store = load_recent_history_store()
    return store.get(client_id, [])


def save_persistent_history(history: list[dict[str, Any]]) -> None:
    client_id = get_history_client_id()
    store = load_recent_history_store()
    store[client_id] = history
    save_recent_history_store(store)


def get_recent_task_history() -> list[dict[str, Any]]:
    require_streamlit()
    history = load_persistent_history()
    history = prune_recent_history(history)
    st.session_state[RECENT_TASK_HISTORY_KEY] = history
    save_persistent_history(history)
    return history


def build_recent_task_entry(task: Any, notion_base_url: str | None) -> dict[str, Any]:
    notion_display = get_notion_display(task, notion_base_url)
    notion_url = notion_display["url"] if notion_display.get("status") == "link" else None
    title = getattr(task, "title", None) or getattr(task, "url", "") or ""
    return {
        "id": str(getattr(task, "id", "")),
        "title": title,
        "url": getattr(task, "url", "") or "",
        "notion_url": notion_url,
        "viewed_at": datetime.utcnow().isoformat(),
    }


def record_recent_task(task: Any, notion_base_url: str | None) -> None:
    history = get_recent_task_history()
    entry = build_recent_task_entry(task, notion_base_url)
    task_id = entry.get("id")
    history = [item for item in history if item.get("id") != task_id]
    history.insert(0, entry)
    st.session_state[RECENT_TASK_HISTORY_KEY] = history
    save_persistent_history(history)


def record_recent_task_entry(entry: dict[str, Any]) -> None:
    history = get_recent_task_history()
    task_id = str(entry.get("id", ""))
    refreshed = {
        **entry,
        "id": task_id,
        "viewed_at": datetime.utcnow().isoformat(),
    }
    history = [item for item in history if str(item.get("id")) != task_id]
    history.insert(0, refreshed)
    st.session_state[RECENT_TASK_HISTORY_KEY] = history
    save_persistent_history(history)


def get_viewed_task_ids() -> set[str]:
    history = get_recent_task_history()
    return {str(item.get("id")) for item in history if item.get("id")}


def open_notion_link(notion_url: str) -> None:
    require_streamlit()
    st.components.v1.html(
        f"<script>window.open({json.dumps(notion_url)}, '_blank')</script>",
        height=0,
    )
