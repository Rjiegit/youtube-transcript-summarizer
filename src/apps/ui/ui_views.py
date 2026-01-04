from __future__ import annotations

import math
from datetime import timezone, timedelta
from typing import Any, Dict

from src.apps.ui.ui_api import (
    call_create_task_api,
    call_processing_api,
    call_processing_lock_release,
    call_processing_lock_status,
    call_retry_task_api,
    get_processing_lock_admin_token,
)
from src.apps.ui.ui_config import NOTION_BASE_URL
from src.apps.ui.ui_history import (
    get_recent_task_history,
    get_viewed_task_ids,
    open_notion_link,
    record_recent_task,
)
from src.apps.ui.ui_notion import get_notion_display
from src.apps.ui.ui_runtime import RequestException, require_streamlit, st
from src.apps.ui.ui_tasks import (
    collect_task_status_options,
    filter_tasks_by_status,
    sort_tasks_for_display,
)
from src.core.utils.url import is_valid_youtube_url, normalize_youtube_url
from src.infrastructure.persistence.factory import DBFactory


def trigger_processing_via_api(db_choice: str) -> None:
    """Trigger the FastAPI worker endpoint and surface result in the UI."""
    require_streamlit()
    payload = {"db_type": db_choice.lower()}

    try:
        with st.spinner("正在排程背景處理..."):
            status, body = call_processing_api(payload)
    except RequestException as exc:
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


def retry_task_via_api(task_id: str, db_choice: str) -> None:
    """Create a retry task for a failed item via the API."""
    require_streamlit()
    payload = {"db_type": db_choice.lower()}

    try:
        with st.spinner("正在建立重試任務..."):
            status, body = call_retry_task_api(task_id, payload)
    except RequestException as exc:
        st.error(f"無法連線至 API：{exc}")
        return

    if status == 201:
        new_task_id = body.get("task_id")
        message = body.get("message") or "已建立重試任務。"
        note = f"{message}（task: {new_task_id}）" if new_task_id else message
        st.toast(note, icon="✅")
        trigger_processing_via_api(db_choice)
        return

    detail = body.get("detail") or body.get("message") or "建立重試任務失敗"
    icon = "ℹ️" if status == 409 else "❌"
    st.toast(f"{detail} (status {status})", icon=icon)


def _maybe_show_lock_snapshot() -> None:
    require_streamlit()
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


def query_processing_lock(db_choice: str) -> None:
    require_streamlit()
    maintainer_token = get_processing_lock_admin_token()
    if not maintainer_token:
        st.warning("未設定 PROCESSING_LOCK_ADMIN_TOKEN，無法查詢 Processing Lock。")
        return

    try:
        status, body = call_processing_lock_status(db_choice, maintainer_token)
    except RequestException as exc:
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
    expected_worker: str,
    reason: str,
    force: bool,
    force_threshold: int,
) -> None:
    require_streamlit()
    maintainer_token = get_processing_lock_admin_token()
    if not maintainer_token:
        st.warning("未設定 PROCESSING_LOCK_ADMIN_TOKEN，無法釋放 Processing Lock。")
        return

    payload: Dict[str, Any] = {"reason": reason or None}
    if expected_worker:
        payload["expected_worker_id"] = expected_worker
    if force:
        payload["force"] = True
        payload["force_threshold_seconds"] = force_threshold

    try:
        status, body = call_processing_lock_release(
            db_choice,
            payload,
            maintainer_token,
        )
    except RequestException as exc:
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


def add_url_callback(db_choice: str) -> None:
    require_streamlit()
    url = st.session_state.url_input
    if url:
        normalized = normalize_youtube_url(url)
        if not normalized or not is_valid_youtube_url(normalized):
            st.toast("Invalid YouTube URL", icon="❌")
            return
        payload = {"url": normalized, "db_type": db_choice.lower()}
        try:
            with st.spinner("正在新增任務並排程背景處理..."):
                status, body = call_create_task_api(payload)
        except RequestException as exc:
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


def main_view() -> None:
    require_streamlit()
    st.title("YouTube Transcript Summarizer")

    st.markdown(
        """
        <style>
        div[data-testid="stButton"] > button[kind="primary"] {
            background-color: #1f6feb;
            border-color: #1f6feb;
            color: #ffffff;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background-color: #1158c7;
            border-color: #1158c7;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.header("Add YouTube URL to Queue")
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
        st.caption("Processing Lock 維運請求會自動使用 `.env` 的 PROCESSING_LOCK_ADMIN_TOKEN。")
        if not get_processing_lock_admin_token():
            st.warning("尚未設定 PROCESSING_LOCK_ADMIN_TOKEN，維運請求將不會送出。")

        if st.button("查詢 Processing Lock", key="lock_status_btn"):
            query_processing_lock(db_choice)

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
                expected_worker,
                reason,
                force,
                int(force_threshold),
            )

    db = DBFactory.get_db(db_choice)

    get_recent_task_history()

    st.header("Tasks in Database")

    tasks = sort_tasks_for_display(db.get_all_tasks())

    if not tasks:
        st.write("No tasks in the database.")
    else:
        status_options = collect_task_status_options(tasks)
        if status_options:
            default_statuses = [
                status
                for status in ["Pending", "Processing", "Completed", "Failed"]
                if status in status_options
            ]
            if "task_status_filter" in st.session_state:
                st.session_state.task_status_filter = [
                    status
                    for status in st.session_state.task_status_filter
                    if status in status_options
                ]
            st.markdown(
                """
                <style>
                .stMultiSelect [data-baseweb="tag"] {
                    background-color: #1f6feb;
                    color: #ffffff;
                }
                .stMultiSelect [data-baseweb="tag"]:hover {
                    background-color: #1158c7;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            selected_statuses = st.multiselect(
                "狀態篩選",
                status_options,
                default=default_statuses,
                key="task_status_filter",
            )
        else:
            selected_statuses = None
        filtered_tasks = filter_tasks_by_status(tasks, selected_statuses)
        if not filtered_tasks:
            st.write("沒有符合狀態篩選的任務。")
            return

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

        total_pages = math.ceil(len(filtered_tasks) / st.session_state.page_size)
        if st.session_state.current_page > total_pages:
            st.session_state.current_page = total_pages
        start_idx = (st.session_state.current_page - 1) * st.session_state.page_size
        end_idx = start_idx + st.session_state.page_size
        paginated_tasks = filtered_tasks[start_idx:end_idx]
        viewed_ids = set(get_viewed_task_ids())

        header_cols = st.columns(8)
        header_cols[0].write("**URL**")
        header_cols[1].write("**Title**")
        header_cols[2].write("**Viewed**")
        header_cols[3].write("**Status**")
        header_cols[4].write("**Created At (Taipei)**")
        header_cols[5].write("**Duration (s)**")
        header_cols[6].write("**Notion**")
        header_cols[7].write("**Action**")

        for task in paginated_tasks:
            col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)
            col1.write(task.url)
            col2.write(task.title)
            viewed_placeholder = col3.empty()
            task_id_str = str(task.id)
            viewed_label = "已看過" if task_id_str in viewed_ids else "-"
            viewed_placeholder.write(viewed_label)
            col4.write(task.status)
            if task.created_at:
                taipei_time = task.created_at.astimezone(timezone(timedelta(hours=8)))
                col5.write(taipei_time.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                col5.write("-")
            if task.status == "Completed" and task.processing_duration is not None:
                col6.write(f"{task.processing_duration:.2f}")
            else:
                col6.write("-")

            notion_display = get_notion_display(task, NOTION_BASE_URL)
            if notion_display["status"] == "link":
                if col7.button("Notion", key=f"notion_{task.id}"):
                    record_recent_task(task, NOTION_BASE_URL)
                    open_notion_link(notion_display["url"])
                    if task_id_str not in viewed_ids:
                        viewed_ids.add(task_id_str)
                        viewed_placeholder.write("已看過")
            elif notion_display["status"] == "invalid":
                col7.write(f"⚠️ {notion_display['message']}")
            else:
                col7.write(notion_display["message"])

            if col8.button("View", key=f"view_{task.id}"):
                record_recent_task(task, NOTION_BASE_URL)
                st.session_state.selected_task_id = task.id
                st.session_state.selected_db_choice = db_choice
                st.rerun()
            if task.status == "Failed":
                if col8.button("Retry", key=f"retry_{task.id}"):
                    retry_task_via_api(task.id, db_choice)

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


def detail_view(task_id: str, db_choice: str) -> None:
    require_streamlit()
    st.title("Task Details")
    db = DBFactory.get_db(db_choice)
    task = db.get_task_by_id(task_id)

    if task:
        record_recent_task(task, NOTION_BASE_URL)
        st.write(f"**URL:** {task.url}")
        st.write(f"**Title:** {task.title}")
        st.write(f"**Status:** {task.status}")
        if task.processing_duration is not None:
            st.write(f"**Processing Duration:** {task.processing_duration:.2f} seconds")
        notion_display = get_notion_display(task, NOTION_BASE_URL)
        if notion_display["status"] == "link":
            st.write("**Notion:**")
            if st.button("Open Notion", key=f"detail_notion_{task.id}"):
                record_recent_task(task, NOTION_BASE_URL)
                open_notion_link(notion_display["url"])
        elif notion_display["status"] == "invalid":
            st.write(f"**Notion:** {notion_display['message']}")
        else:
            st.write(f"**Notion:** {notion_display['message']}")
        st.header("Summary")
        st.markdown(task.summary)
    else:
        st.error("Task not found.")

    if st.button("Back to Main View"):
        del st.session_state.selected_task_id
        if "selected_db_choice" in st.session_state:
            del st.session_state.selected_db_choice
        st.rerun()
