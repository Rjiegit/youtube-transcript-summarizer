# ruff: noqa: E402 - streamlit needs top-level imports
import os
import math
import sys
from datetime import timezone, timedelta
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:  # ensure src package can be imported when run via path
    sys.path.insert(0, str(ROOT_DIR))

import requests
import streamlit as st

from src.core.utils.url import normalize_youtube_url, is_valid_youtube_url
from src.infrastructure.persistence.factory import DBFactory

API_BASE_URL = os.environ.get("TASK_API_BASE_URL", "http://localhost:8080")


def _call_create_task_api(payload: Dict[str, Any]) -> tuple[int, Dict[str, Any]]:
    """Send POST to /tasks and return status + payload."""
    endpoint = f"{API_BASE_URL.rstrip('/')}/tasks"
    response = requests.post(endpoint, json=payload, timeout=10)
    try:
        body: Dict[str, Any] = response.json()
    except ValueError:
        body = {}
    return response.status_code, body


def _call_processing_api(payload: Dict[str, Any]) -> tuple[int, Dict[str, Any]]:
    """Send POST to /processing-jobs and return status + payload."""
    endpoint = f"{API_BASE_URL.rstrip('/')}/processing-jobs"
    response = requests.post(endpoint, json=payload, timeout=10)
    try:
        body: Dict[str, Any] = response.json()
    except ValueError:
        body = {}
    return response.status_code, body


def _call_processing_lock_status(
    db_choice: str, maintainer_token: str | None
) -> tuple[int, Dict[str, Any]]:
    endpoint = f"{API_BASE_URL.rstrip('/')}/processing-lock"
    headers = {"X-Maintainer-Token": maintainer_token} if maintainer_token else {}
    params = {"db_type": db_choice.lower()}

    response = requests.get(endpoint, headers=headers, params=params, timeout=10)
    try:
        body: Dict[str, Any] = response.json()
    except ValueError:
        body = {}
    return response.status_code, body


def _call_processing_lock_release(
    db_choice: str,
    maintainer_token: str | None,
    payload: Dict[str, Any],
) -> tuple[int, Dict[str, Any]]:
    endpoint = f"{API_BASE_URL.rstrip('/')}/processing-lock"
    headers = {"X-Maintainer-Token": maintainer_token} if maintainer_token else {}
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


def trigger_processing_via_api(db_choice: str):
    """Trigger the FastAPI worker endpoint and surface result in the UI."""
    payload = {"db_type": db_choice.lower()}

    try:
        with st.spinner("正在排程背景處理..."):
            status, body = _call_processing_api(payload)
    except requests.RequestException as exc:
        st.error(f"無法連線至 API：{exc}")
        return

    if status == 202:
        worker_id = body.get("worker_id")
        message = body.get("message", "已排程背景處理。")
        note = f"{message}（worker: {worker_id}）" if worker_id else message
        st.toast(note, icon="✅")
    elif status == 409:
        detail = body.get("detail") or body.get("message") or "背景處理已在進行中。"
        st.toast(detail, icon="ℹ️")
    else:
        detail = body.get("detail") or body.get("message") or "未知錯誤"
        st.error(f"啟動背景處理失敗：{detail}")


def _maybe_show_lock_snapshot() -> None:
    snapshot = st.session_state.get("processing_lock_snapshot")
    if not snapshot:
        return

    st.markdown("**最近一次 lock 狀態**")
    if not snapshot.get("worker_id"):
        st.success("目前沒有持有者。")
        return

    age_value = snapshot.get("age_seconds")
    st.write(
        f"- Worker: `{snapshot.get('worker_id')}`\n"
        f"- Locked At: {snapshot.get('locked_at')}\n"
        f"- Age (秒): {age_value if age_value is not None else '-'}\n"
        f"- Stale: {snapshot.get('stale')}"
    )


def query_processing_lock(db_choice: str, maintainer_token: str) -> None:
    if not maintainer_token:
        st.warning("請先輸入 X-Maintainer-Token 才能查詢 lock。")
        return

    try:
        status, body = _call_processing_lock_status(db_choice, maintainer_token)
    except requests.RequestException as exc:
        st.error(f"查詢 lock 失敗：{exc}")
        return

    if status == 200:
        snapshot = body.get("snapshot") or {}
        st.session_state.processing_lock_snapshot = snapshot
        st.success("已取得 lock 狀態。")
        _maybe_show_lock_snapshot()
    else:
        detail = body.get("detail") or body.get("message") or "查詢失敗"
        st.error(f"{detail} (status {status})")


def release_processing_lock(
    db_choice: str,
    maintainer_token: str,
    expected_worker: str,
    reason: str,
    force: bool,
    force_threshold: int,
) -> None:
    if not maintainer_token:
        st.warning("請先輸入 X-Maintainer-Token 才能釋放 lock。")
        return

    payload: Dict[str, Any] = {"reason": reason or None}
    if expected_worker:
        payload["expected_worker_id"] = expected_worker
    if force:
        payload["force"] = True
        payload["force_threshold_seconds"] = force_threshold

    try:
        status, body = _call_processing_lock_release(
            db_choice,
            maintainer_token,
            payload,
        )
    except requests.RequestException as exc:
        st.error(f"釋放 lock 失敗：{exc}")
        return

    if status == 200:
        st.success("Processing lock 已更新。")
        after_snapshot = body.get("after") or {}
        st.session_state.processing_lock_snapshot = after_snapshot
        st.info(body.get("reason") or "Lock 釋放完成")
        _maybe_show_lock_snapshot()
    else:
        detail = body.get("detail") or body.get("message") or "操作失敗"
        st.error(f"{detail} (status {status})")


def add_url_callback(db_choice):
    url = st.session_state.url_input
    if url:
        normalized = normalize_youtube_url(url)
        if not normalized or not is_valid_youtube_url(normalized):
            st.toast("Invalid YouTube URL", icon="❌")
            return
        payload = {"url": normalized, "db_type": db_choice.lower()}
        try:
            with st.spinner("正在新增任務並排程背景處理..."):
                status, body = _call_create_task_api(payload)
        except requests.RequestException as exc:
            st.error(f"無法連線至 API：{exc}")
            return

        if status == 201:
            message = body.get(
                "message",
                f"Successfully added to queue: {normalized}",
            )
            icon = "✅" if body.get("processing_started", False) else "ℹ️"
            st.toast(message, icon=icon)
            st.session_state.url_input = ""
        else:
            detail = body.get("detail") or body.get("message") or "新增任務失敗。"
            icon = "ℹ️" if status == 409 else "❌"
            st.toast(f"{detail} (status {status})", icon=icon)
    else:
        st.toast("Please enter a URL", icon="❌")


def main_view():
    st.title("YouTube Transcript Summarizer")

    # Section for adding URLs to the queue
    st.header("Add YouTube URL to Queue")
    # Use a single database selection for the entire view
    db_choice = st.selectbox("Select Database", ["SQLite", "Notion"], key="db_choice")

    st.text_input("Enter YouTube URL", key="url_input")

    col1, col2, _ = st.columns([2, 3, 2])
    with col1:
        st.button(
            "Add to Queue",
            on_click=add_url_callback,
            args=(db_choice,),
            use_container_width=True,
        )
    with col2:
        if st.button(
            "Trigger Background Processing",
            use_container_width=True,
            type="primary",
        ):
            trigger_processing_via_api(db_choice)

    with st.expander("Processing Lock 管理（維運專用）"):
        lock_token = st.text_input(
            "X-Maintainer-Token",
            type="password",
            key="lock_admin_token_input",
        )
        st.caption("透過維運端點查詢或釋放 Processing Lock。Token 來自 `.env` 的 PROCESSING_LOCK_ADMIN_TOKEN。")

        if st.button("查詢 Processing Lock", key="lock_status_btn"):
            query_processing_lock(db_choice, lock_token)

        _maybe_show_lock_snapshot()

        st.divider()

        expected_worker = st.text_input(
            "預期的 worker_id（非必要）",
            key="lock_expected_worker",
        )
        reason = st.text_input(
            "釋放理由",
            key="lock_release_reason",
        )
        force = st.checkbox(
            "強制釋放（需搭配 force_threshold_seconds）",
            key="lock_force_checkbox",
        )
        force_threshold = st.number_input(
            "Force threshold (秒)",
            min_value=0,
            value=1200,
            step=60,
            key="lock_force_threshold",
        )

        if st.button("釋放 Processing Lock", key="lock_release_btn"):
            release_processing_lock(
                db_choice,
                lock_token,
                expected_worker,
                reason,
                force,
                int(force_threshold),
            )

    # Section for displaying tasks
    st.header("Tasks in Database")
    # Reuse the same database selection for viewing tasks
    db = DBFactory.get_db(db_choice)

    tasks = db.get_all_tasks()

    if not tasks:
        st.write("No tasks in the database.")
    else:
        # Sort tasks by created_at in descending order
        tasks.sort(key=lambda x: x.created_at, reverse=True)

        # Pagination
        if "page_size" not in st.session_state:
            st.session_state.page_size = 20
        if "current_page" not in st.session_state:
            st.session_state.current_page = 1

        page_size = st.selectbox(
            "Items per page",
            [20, 50, 100],
            index=[20, 50, 100].index(st.session_state.page_size),
            key="page_size_selector",
        )
        st.session_state.page_size = page_size

        total_pages = math.ceil(len(tasks) / st.session_state.page_size)
        start_idx = (st.session_state.current_page - 1) * st.session_state.page_size
        end_idx = start_idx + st.session_state.page_size
        paginated_tasks = tasks[start_idx:end_idx]

        # Display tasks in a table-like format
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.write("**URL**")
        col2.write("**Title**")
        col3.write("**Status**")
        col4.write("**Created At (Taipei)**")
        col5.write("**Duration (s)**")  # New column
        col6.write("**Action**")

        for task in paginated_tasks:
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.write(task.url)
            col2.write(task.title)
            col3.write(task.status)
            taipei_time = task.created_at.astimezone(timezone(timedelta(hours=8)))
            col4.write(taipei_time.strftime("%Y-%m-%d %H:%M:%S"))
            # Display duration if available and task is completed
            if task.status == "Completed" and task.processing_duration is not None:
                col5.write(f"{task.processing_duration:.2f}")
            else:
                col5.write("-")  # Or some other placeholder
            if col6.button("View", key=f"view_{task.id}"):
                st.session_state.selected_task_id = task.id
                # Store selection under a different key to avoid
                # modifying the widget-backed session key "db_choice".
                st.session_state.selected_db_choice = db_choice
                st.rerun()

        # Pagination controls
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Previous"):
                if st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
                    st.rerun()
        with col2:
            st.write(f"Page {st.session_state.current_page} of {total_pages}")
        with col3:
            if st.button("Next"):
                if st.session_state.current_page < total_pages:
                    st.session_state.current_page += 1
                    st.rerun()


def detail_view(task_id, db_choice):
    st.title("Task Details")
    db = DBFactory.get_db(db_choice)
    task = db.get_task_by_id(task_id)

    if task:
        st.write(f"**URL:** {task.url}")
        st.write(f"**Title:** {task.title}")
        st.write(f"**Status:** {task.status}")
        if task.processing_duration is not None:
            st.write(f"**Processing Duration:** {task.processing_duration:.2f} seconds")
        st.header("Summary")
        st.markdown(task.summary)
    else:
        st.error("Task not found.")

    if st.button("Back to Main View"):
        del st.session_state.selected_task_id
        if "selected_db_choice" in st.session_state:
            del st.session_state.selected_db_choice
        st.rerun()


if __name__ == "__main__":
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
