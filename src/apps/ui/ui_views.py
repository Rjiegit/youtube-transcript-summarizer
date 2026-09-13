from __future__ import annotations

import math
from datetime import timezone, timedelta

from src.apps.ui.ui_api import (
    call_create_task_api,
)
from src.apps.ui.ui_config import NOTION_BASE_URL
from src.apps.ui.ui_history import (
    get_recent_task_history,
    get_viewed_task_ids,
    open_notion_link,
    record_recent_task,
)
from src.apps.ui.ui_rss import (
    add_rss_subscription,
    format_rss_poll_results,
    trigger_rss_poll_once,
    update_rss_subscription,
)
from src.apps.ui.ui_notion import get_notion_display
from src.apps.ui.ui_runtime import RequestException, require_streamlit, st
from src.apps.ui.ui_tasks import (
    collect_task_status_options,
    filter_tasks_by_status,
    sort_tasks_for_display,
)
from src.core.utils.url import is_valid_youtube_url, normalize_youtube_url
from src.infrastructure.repository_composition import create_database, create_rss_repository
from src.infrastructure.persistence.sqlite.client import SQLiteDB


from src.apps.ui.ui_processing import (
    _maybe_show_lock_snapshot,
    build_force_release_payload,
    build_targeted_release_payload,
    get_processing_lock_admin_token,
    get_snapshot_worker_id,
    query_processing_lock,
    release_processing_lock_with_payload,
    retry_task_via_api,
    trigger_processing_via_api,
)


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


def render_rss_management(db) -> None:
    require_streamlit()
    st.header("RSS Channel Management")
    if not isinstance(db, SQLiteDB):
        st.caption("RSS monitor 目前僅支援 SQLite。")
        return

    st.caption(
        "首次新增或首次啟用 RSS 訂閱時，系統只會從當下開始建立監控基準，"
        "不會自動補抓該 channel 既有的歷史影片。"
    )

    repository = create_rss_repository(db.db_path)

    manual_poll_col, _ = st.columns([2, 5])
    if manual_poll_col.button(
        "手動執行一次 RSS 監控",
        key="rss_poll_once_button",
        type="primary",
        use_container_width=True,
    ):
        try:
            with st.spinner("正在執行 RSS 輪詢..."):
                results = trigger_rss_poll_once(db.db_path)
            summary_lines = format_rss_poll_results(results)
            if summary_lines:
                st.session_state.rss_poll_summary = summary_lines
                st.toast("RSS 輪詢完成。", icon="✅")
            else:
                st.session_state.rss_poll_summary = ["沒有啟用中的 RSS 訂閱。"]
                st.toast("沒有啟用中的 RSS 訂閱。", icon="ℹ️")
            st.rerun()
        except Exception as exc:
            st.error(f"RSS 輪詢失敗：{exc}")

    summary_lines = st.session_state.get("rss_poll_summary")
    if summary_lines:
        st.info("\n".join(summary_lines))

    with st.form("rss_add_form", clear_on_submit=True):
        rss_input = st.text_input("Channel ID 或 Feed URL", key="rss_add_input")
        rss_title = st.text_input("顯示名稱（可選）", key="rss_add_title")
        rss_enabled = st.checkbox("新增後啟用", value=True, key="rss_add_enabled")
        submitted = st.form_submit_button("新增 RSS 訂閱")
        if submitted:
            try:
                add_rss_subscription(
                    repository,
                    rss_input,
                    title=rss_title,
                    enabled=rss_enabled,
                )
                st.toast(
                    "RSS 訂閱已新增。首次啟用只會從目前時間點後開始監控，不會補抓舊影片。",
                    icon="✅",
                )
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    subscriptions = repository.list_subscriptions()
    if not subscriptions:
        st.caption("目前尚無 RSS 訂閱。")
        return

    for subscription in subscriptions:
        label = subscription.title or subscription.channel_id
        with st.expander(f"{label} | {'Enabled' if subscription.enabled else 'Disabled'}"):
            st.write(f"Feed URL: {subscription.feed_url}")
            st.write(f"Last Checked: {subscription.last_checked_at or '-'}")
            st.write(f"Last Status: {subscription.last_status or '-'}")
            st.write(f"Last Error: {subscription.last_error or '-'}")

            edit_key = f"rss_edit_{subscription.id}"
            with st.form(edit_key):
                raw_value = st.text_input(
                    "Channel ID 或 Feed URL",
                    value=subscription.feed_url,
                    key=f"{edit_key}_value",
                )
                title = st.text_input(
                    "顯示名稱",
                    value=subscription.title,
                    key=f"{edit_key}_title",
                )
                enabled = st.checkbox(
                    "啟用",
                    value=subscription.enabled,
                    key=f"{edit_key}_enabled",
                )
                save_clicked = st.form_submit_button("儲存變更")
                if save_clicked:
                    try:
                        update_rss_subscription(
                            repository,
                            subscription.id,
                            raw_value,
                            title=title,
                            enabled=enabled,
                        )
                        st.toast("RSS 訂閱已更新。", icon="✅")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))

            action_cols = st.columns(2)
            toggle_label = "停用" if subscription.enabled else "啟用"
            if action_cols[0].button(toggle_label, key=f"rss_toggle_{subscription.id}"):
                repository.set_enabled(subscription.id, not subscription.enabled)
                st.rerun()
            if action_cols[1].button("刪除", key=f"rss_delete_{subscription.id}"):
                repository.delete_subscription(subscription.id)
                st.rerun()


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
        snapshot = st.session_state.get("processing_lock_snapshot") or {}
        snapshot_worker_id = get_snapshot_worker_id(snapshot)

        st.divider()

        expected_worker = st.text_input(
            "指定 worker_id（可選，未填則優先使用最近查詢到的 worker）",
            key="lock_expected_worker",
        )
        reason = st.text_input(
            "釋放理由",
            key="lock_release_reason",
        )
        force_threshold = st.number_input(
            "強制釋放門檻（秒）",
            min_value=0,
            value=1200,
            step=60,
            key="lock_force_threshold",
        )

        action_col_1, action_col_2 = st.columns(2)
        with action_col_1:
            if st.button(
                "釋放目前 worker 的 lock",
                key="lock_release_targeted_btn",
                use_container_width=True,
            ):
                payload = build_targeted_release_payload(
                    manual_worker_id=expected_worker,
                    snapshot_worker_id=snapshot_worker_id,
                    reason=reason,
                )
                if payload is None:
                    st.warning("請先查詢 lock 狀態，或手動輸入要釋放的 worker_id。")
                else:
                    release_processing_lock_with_payload(db_choice, payload)

        with action_col_2:
            if st.button(
                "一鍵強制清空 Processing Lock",
                key="lock_release_force_btn",
                type="primary",
                use_container_width=True,
            ):
                payload = build_force_release_payload(
                    reason=reason,
                    force_threshold=int(force_threshold),
                )
                release_processing_lock_with_payload(db_choice, payload)

    db = create_database(db_choice)

    render_rss_management(db)

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
    db = create_database(db_choice)
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
