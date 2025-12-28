# ruff: noqa: E402 - streamlit needs top-level imports
from __future__ import annotations

import sys
from pathlib import Path

try:  # pragma: no cover - optional for local runs
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - allow running without python-dotenv
    def load_dotenv(*_args, **_kwargs):
        return False

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:  # ensure src package can be imported when run via path
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv()

from src.apps.ui.ui_history import (
    build_recent_task_entry,
    prune_recent_history,
    record_recent_task_entry,
)
from src.apps.ui.ui_notion import build_notion_url, get_notion_display
from src.apps.ui.ui_config import RECENT_TASK_HISTORY_TTL_DAYS
from src.apps.ui.ui_runtime import require_streamlit, st
from src.apps.ui.ui_tasks import (
    collect_task_status_options,
    filter_tasks_by_status,
    sort_tasks_for_display,
)
from src.apps.ui.ui_views import detail_view, main_view

__all__ = [
    "build_notion_url",
    "get_notion_display",
    "build_recent_task_entry",
    "record_recent_task_entry",
    "_build_recent_task_entry",
    "_record_recent_task_entry",
    "_prune_recent_history",
    "RECENT_TASK_HISTORY_TTL_DAYS",
    "sort_tasks_for_display",
    "collect_task_status_options",
    "filter_tasks_by_status",
    "main_view",
    "detail_view",
]

_build_recent_task_entry = build_recent_task_entry
_record_recent_task_entry = record_recent_task_entry
_prune_recent_history = prune_recent_history


if __name__ == "__main__":
    require_streamlit()
    if st is not None:
        st.set_page_config(layout="wide")
    if "selected_task_id" in st.session_state:
        # Use a separate session key to carry the db selection
        # into the detail view to avoid conflicting with the
        # selectbox widget key "db_choice" in the main view.
        chosen_db = st.session_state.get(
            "selected_db_choice",
            st.session_state.get("db_choice", "SQLite"),
        )
        detail_view(st.session_state.selected_task_id, chosen_db)
    else:
        main_view()
