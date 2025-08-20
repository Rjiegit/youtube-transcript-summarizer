"""Queue state initialization and helpers for dynamic batch processing."""
from __future__ import annotations
import streamlit as st
from typing import Dict, Any
from datetime import datetime, timezone

STATE_KEY = "dynamic_queue"

EMPTY_STATE: Dict[str, Any] = {
    "current_url_input": "",
    "task_queue": [],           # list of task dicts
    "current_index": 0,         # index of next task to process
    "is_processing": False,     # processing flag
    "should_stop": False,       # graceful stop flag
    "results": [],              # list of result dicts
    "error_log": [],            # list of error dicts
    "stats": {                  # cached counters
        "total": 0,
        "waiting": 0,
        "processing": 0,
        "completed": 0,
        "failed": 0,
    }
}

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def init_dynamic_queue_state(force: bool = False) -> None:
    """Initialize session state structure for dynamic queue if absent or forced."""
    if force or STATE_KEY not in st.session_state:
        # deep copy to avoid accidental shared mutations
        st.session_state[STATE_KEY] = {
            k: (v.copy() if isinstance(v, dict) else list(v) if isinstance(v, list) else v)
            for k, v in EMPTY_STATE.items()
        }

def reset_dynamic_queue_state() -> None:
    """Reset queue state to empty (preserves existing key)."""
    init_dynamic_queue_state(force=True)


def update_stats() -> None:
    """Recalculate statistics based on current task_queue."""
    dq = st.session_state.get(STATE_KEY)
    if not dq:
        return
    waiting = processing = completed = failed = 0
    for t in dq["task_queue"]:
        status = t.get("status")
        if status == "waiting":
            waiting += 1
        elif status == "processing":
            processing += 1
        elif status == "completed":
            completed += 1
        elif status == "failed":
            failed += 1
    dq["stats"] = {
        "total": len(dq["task_queue"]),
        "waiting": waiting,
        "processing": processing,
        "completed": completed,
        "failed": failed,
    }


def get_queue_state() -> Dict[str, Any]:
    init_dynamic_queue_state()
    return st.session_state[STATE_KEY]
