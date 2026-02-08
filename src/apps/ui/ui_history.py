from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from src.apps.ui.ui_config import RECENT_TASK_HISTORY_KEY, RECENT_TASK_HISTORY_TTL_DAYS
from src.apps.ui.ui_runtime import require_streamlit, st
from src.core.time_utils import utc_now_naive
from src.infrastructure.persistence.sqlite.client import SQLiteDB


def _get_history_db() -> SQLiteDB:
    return SQLiteDB()


def prune_recent_history() -> None:
    cutoff = utc_now_naive() - timedelta(days=RECENT_TASK_HISTORY_TTL_DAYS)
    _get_history_db().prune_recent_task_history(cutoff)


def get_recent_task_history() -> list[dict[str, Any]]:
    require_streamlit()
    prune_recent_history()
    history = _get_history_db().list_recent_task_history()
    st.session_state[RECENT_TASK_HISTORY_KEY] = history
    return history


def build_recent_task_entry(task: Any, _notion_base_url: str | None) -> dict[str, Any]:
    return {
        "id": str(getattr(task, "id", "")),
        "viewed_at": utc_now_naive().isoformat(),
    }


def record_recent_task(task: Any, _notion_base_url: str | None) -> None:
    entry = build_recent_task_entry(task, None)
    task_id = entry.get("id") or ""
    _get_history_db().record_recent_task_view(task_id)
    get_recent_task_history()


def record_recent_task_entry(entry: dict[str, Any]) -> None:
    task_id = str(entry.get("id", ""))
    if not task_id:
        return
    _get_history_db().record_recent_task_view(task_id)
    get_recent_task_history()


def get_viewed_task_ids() -> set[str]:
    history = get_recent_task_history()
    return {str(item.get("id")) for item in history if item.get("id")}


def open_notion_link(notion_url: str) -> None:
    require_streamlit()
    st.components.v1.html(
        f"<script>window.open({json.dumps(notion_url)}, '_blank')</script>",
        height=0,
    )
