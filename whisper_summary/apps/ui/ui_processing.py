from __future__ import annotations

from typing import Any, Dict

from whisper_summary.apps.ui.ui_api import (
    call_processing_api,
    call_processing_lock_release,
    call_processing_lock_status,
    call_retry_task_api,
    get_processing_lock_admin_token,
)
from whisper_summary.apps.ui.ui_runtime import RequestException, require_streamlit, st


def _normalize_optional_text(value: str | None) -> str | None:
    normalized = (value or "").strip()
    return normalized or None


def get_snapshot_worker_id(snapshot: dict[str, Any] | None) -> str | None:
    if not snapshot:
        return None
    return _normalize_optional_text(snapshot.get("worker_id"))


def build_targeted_release_payload(
    manual_worker_id: str,
    snapshot_worker_id: str | None,
    reason: str,
) -> Dict[str, Any] | None:
    worker_id = _normalize_optional_text(manual_worker_id) or _normalize_optional_text(
        snapshot_worker_id
    )
    if not worker_id:
        return None

    payload: Dict[str, Any] = {"expected_worker_id": worker_id}
    normalized_reason = _normalize_optional_text(reason)
    if normalized_reason:
        payload["reason"] = normalized_reason
    return payload


def build_force_release_payload(reason: str, force_threshold: int) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "force": True,
        "force_threshold_seconds": force_threshold,
    }
    normalized_reason = _normalize_optional_text(reason)
    if normalized_reason:
        payload["reason"] = normalized_reason
    return payload


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


def release_processing_lock_with_payload(
    db_choice: str,
    payload: Dict[str, Any],
) -> None:
    expected_worker = payload.get("expected_worker_id") or ""
    reason = payload.get("reason") or ""
    force = bool(payload.get("force"))
    force_threshold = int(payload.get("force_threshold_seconds") or 0)
    release_processing_lock(
        db_choice=db_choice,
        expected_worker=expected_worker,
        reason=reason,
        force=force,
        force_threshold=force_threshold,
    )



