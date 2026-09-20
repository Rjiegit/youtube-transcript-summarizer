"""Processing job and lock administration endpoints."""

import os
from datetime import timedelta

from fastapi import APIRouter, Header, HTTPException, Response, status

from whisper_summary.apps.api.dependencies import ensure_db_configuration, get_database
from whisper_summary.apps.api.schemas import (
    ProcessingJobCreateRequest,
    ProcessingJobCreateResponse,
    ProcessingLockReleaseRequest,
    ProcessingLockReleaseResponse,
    ProcessingLockSnapshot,
    ProcessingLockStatusResponse,
    ProcessingLeaseFailRequest,
    ProcessingLeaseFailResponse,
    ProcessingLeaseSnapshot,
    ProcessingLeaseStatusResponse,
    WorkerLeaseRequest,
    WorkerTaskClaimRequest,
    WorkerTaskClaimResponse,
    WorkerTaskCompleteRequest,
    WorkerTaskFailRequest,
    WorkerTaskPayload,
    WorkerTaskProgressRequest,
    normalize_db_type,
)
from whisper_summary.core.logger import logger
from whisper_summary.core.time_utils import as_utc, utc_now
from whisper_summary.domain.interfaces.database import ProcessingLockInfo
from whisper_summary.services.pipeline.processing_runner import (
    PROCESSING_LOCK_TIMEOUT_SECONDS,
    TASK_LOCK_TIMEOUT_SECONDS,
)

router = APIRouter()


def ensure_worker_token(token: str | None) -> None:
    expected = os.environ.get("PROCESSING_WORKER_TOKEN") or os.environ.get(
        "PROCESSING_LOCK_ADMIN_TOKEN"
    )
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Processing worker token is not configured.",
        )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing worker token.",
        )
    if token != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid worker token.",
        )


def _require_active_lease(updated: bool) -> None:
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task lease is no longer owned by this worker.",
        )


def _build_task_lease_snapshot(task) -> ProcessingLeaseSnapshot:
    locked_at = as_utc(task.locked_at)
    age_seconds = max(0.0, (utc_now() - locked_at).total_seconds())
    return ProcessingLeaseSnapshot(
        task_id=task.id,
        title=task.title,
        worker_id=task.worker_id,
        locked_at=locked_at,
        age_seconds=age_seconds,
        stale=age_seconds >= TASK_LOCK_TIMEOUT_SECONDS,
    )


@router.post("/worker-tasks/claim")
def claim_worker_task(
    payload: WorkerTaskClaimRequest,
    worker_token: str | None = Header(None, alias="X-Worker-Token"),
):
    ensure_worker_token(worker_token)
    db = get_database("sqlite")
    task = db.acquire_next_task(
        payload.worker_id,
        lock_timeout_seconds=TASK_LOCK_TIMEOUT_SECONDS,
    )
    if task is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    if not task.lease_token or not task.locked_at:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Claimed task is missing lease metadata.",
        )
    return WorkerTaskClaimResponse(
        task=WorkerTaskPayload(
            id=task.id,
            url=task.url,
            status=task.status,
            title=task.title,
            notion_page_id=task.notion_page_id,
            processing_engine=task.processing_engine,
        ),
        lease_token=task.lease_token,
        lease_expires_at=task.locked_at + timedelta(
            seconds=TASK_LOCK_TIMEOUT_SECONDS
        ),
    )


@router.post(
    "/worker-tasks/{task_id}/heartbeat",
    status_code=status.HTTP_204_NO_CONTENT,
)
def heartbeat_worker_task(
    task_id: str,
    payload: WorkerLeaseRequest,
    worker_token: str | None = Header(None, alias="X-Worker-Token"),
) -> Response:
    ensure_worker_token(worker_token)
    db = get_database("sqlite")
    _require_active_lease(
        db.refresh_task_lease(task_id, payload.worker_id, payload.lease_token)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/worker-tasks/{task_id}/progress",
    status_code=status.HTTP_204_NO_CONTENT,
)
def update_worker_task_progress(
    task_id: str,
    payload: WorkerTaskProgressRequest,
    worker_token: str | None = Header(None, alias="X-Worker-Token"),
) -> Response:
    ensure_worker_token(worker_token)
    db = get_database("sqlite")
    _require_active_lease(
        db.update_claimed_task(
            task_id,
            payload.worker_id,
            payload.lease_token,
            status="Processing",
            title=payload.title,
            processing_engine=payload.processing_engine,
        )
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/worker-tasks/{task_id}/complete",
    status_code=status.HTTP_204_NO_CONTENT,
)
def complete_worker_task(
    task_id: str,
    payload: WorkerTaskCompleteRequest,
    worker_token: str | None = Header(None, alias="X-Worker-Token"),
) -> Response:
    ensure_worker_token(worker_token)
    db = get_database("sqlite")
    _require_active_lease(
        db.update_claimed_task(
            task_id,
            payload.worker_id,
            payload.lease_token,
            status="Completed",
            title=payload.title,
            summary=payload.summary,
            processing_duration=payload.processing_duration,
            notion_page_id=payload.notion_page_id,
            processing_engine=payload.processing_engine,
        )
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/worker-tasks/{task_id}/fail",
    status_code=status.HTTP_204_NO_CONTENT,
)
def fail_worker_task(
    task_id: str,
    payload: WorkerTaskFailRequest,
    worker_token: str | None = Header(None, alias="X-Worker-Token"),
) -> Response:
    ensure_worker_token(worker_token)
    db = get_database("sqlite")
    _require_active_lease(
        db.update_claimed_task(
            task_id,
            payload.worker_id,
            payload.lease_token,
            status="Failed",
            error_message=payload.error_message,
            processing_duration=payload.processing_duration,
        )
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/processing-leases",
    response_model=ProcessingLeaseStatusResponse,
)
def get_processing_leases(
    maintainer_token: str | None = Header(None, alias="X-Maintainer-Token"),
) -> ProcessingLeaseStatusResponse:
    ensure_maintainer_token(maintainer_token)
    db = get_database("sqlite")
    return ProcessingLeaseStatusResponse(
        leases=[
            _build_task_lease_snapshot(task)
            for task in db.list_processing_tasks()
            if task.worker_id and task.locked_at
        ]
    )


@router.post(
    "/processing-leases/{task_id}/fail",
    response_model=ProcessingLeaseFailResponse,
)
def fail_processing_lease(
    task_id: str,
    payload: ProcessingLeaseFailRequest,
    maintainer_token: str | None = Header(None, alias="X-Maintainer-Token"),
) -> ProcessingLeaseFailResponse:
    ensure_maintainer_token(maintainer_token)
    db = get_database("sqlite")
    task = db.get_task_by_id(task_id)
    if task is None or task.status != "Processing" or not task.worker_id or not task.locked_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active task lease was not found.",
        )
    before = _build_task_lease_snapshot(task)
    reason = payload.reason or "Manually failed by maintainer"
    if payload.dry_run:
        return ProcessingLeaseFailResponse(
            failed=False,
            reason=reason,
            before=before,
        )
    if not payload.force and payload.expected_worker_id != task.worker_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="expected_worker_id does not match the active lease.",
        )
    if payload.force and before.age_seconds < payload.force_threshold_seconds:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task lease has not aged enough for forced failure.",
        )
    updated = db.fail_processing_task(
        task_id,
        reason,
        expected_worker_id=None if payload.force else task.worker_id,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task lease changed before it could be failed.",
        )
    return ProcessingLeaseFailResponse(
        failed=True,
        reason=reason,
        before=before,
    )


def ensure_maintainer_token(token: str | None) -> None:
    admin_token = os.environ.get("PROCESSING_LOCK_ADMIN_TOKEN")
    if not admin_token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Processing lock admin token is not configured.")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing maintainer token.")
    if token != admin_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid maintainer token.")


def build_lock_snapshot(info: ProcessingLockInfo) -> ProcessingLockSnapshot:
    now = utc_now()
    age_seconds: float | None = None
    locked_at = None
    if info.locked_at:
        locked_at = as_utc(info.locked_at)
        age_seconds = max(0.0, (now - locked_at).total_seconds())
    stale = age_seconds is not None and age_seconds >= PROCESSING_LOCK_TIMEOUT_SECONDS
    return ProcessingLockSnapshot(worker_id=info.worker_id, locked_at=locked_at, age_seconds=age_seconds, stale=stale)


@router.post(
    "/processing-jobs",
    response_model=ProcessingJobCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_processing_job_endpoint(
    payload: ProcessingJobCreateRequest,
) -> ProcessingJobCreateResponse:
    """Confirm that the persisted queue is handled by the dedicated worker."""

    ensure_db_configuration(payload.db_type)
    return ProcessingJobCreateResponse(
        worker_id=payload.worker_id or "processing-worker",
        db_type=payload.db_type,
        accepted=True,
        message="Dedicated processing worker polls the persisted queue.",
    )


@router.get(
    "/processing-lock",
    response_model=ProcessingLockStatusResponse,
    status_code=status.HTTP_200_OK,
)
def get_processing_lock_status(
    db_type: str = "sqlite",
    maintainer_token: str | None = Header(None, alias="X-Maintainer-Token"),
) -> ProcessingLockStatusResponse:
    """Inspect the current processing lock for the selected backend."""

    normalized_db_type = normalize_db_type(db_type)
    ensure_maintainer_token(maintainer_token)
    ensure_db_configuration(normalized_db_type)
    db = get_database(normalized_db_type)
    snapshot = build_lock_snapshot(db.read_processing_lock())
    logger.info(
        f"Maintainer inspected processing lock for {normalized_db_type} "
        f"(worker={snapshot.worker_id}, stale={snapshot.stale})"
    )
    return ProcessingLockStatusResponse(
        db_type=normalized_db_type,
        snapshot=snapshot,
    )


@router.delete(
    "/processing-lock",
    response_model=ProcessingLockReleaseResponse,
    status_code=status.HTTP_200_OK,
)
def delete_processing_lock(
    payload: ProcessingLockReleaseRequest,
    maintainer_token: str | None = Header(None, alias="X-Maintainer-Token"),
) -> ProcessingLockReleaseResponse:
    """Attempt to release the global processing lock, optionally forcing it."""

    ensure_maintainer_token(maintainer_token)
    ensure_db_configuration(payload.db_type)
    db = get_database(payload.db_type)
    before_info = db.read_processing_lock()
    before_snapshot = build_lock_snapshot(before_info)

    if not before_info.worker_id:
        logger.info(
            f"Processing lock release requested for {payload.db_type} "
            "but no lock was present."
        )
        return ProcessingLockReleaseResponse(
            db_type=payload.db_type,
            released=False,
            reason="lock_not_found",
            before=before_snapshot,
            after=before_snapshot,
        )

    if payload.dry_run:
        logger.info(
            f"Processing lock dry-run for {payload.db_type} (worker={before_info.worker_id})."
        )
        return ProcessingLockReleaseResponse(
            db_type=payload.db_type,
            released=False,
            reason=payload.reason or "dry_run",
            before=before_snapshot,
            after=before_snapshot,
        )

    if payload.force:
        threshold = payload.force_threshold_seconds or 0
        lock_age = before_snapshot.age_seconds or 0.0
        if threshold > 0 and lock_age < threshold:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Processing lock has not aged enough for a forced release.",
            )

        db.clear_processing_lock()
        after_snapshot = build_lock_snapshot(db.read_processing_lock())
        logger.info(
            f"Processing lock force-released for {payload.db_type} "
            f"(worker={before_info.worker_id}, reason={payload.reason})"
        )
        return ProcessingLockReleaseResponse(
            db_type=payload.db_type,
            released=True,
            reason=payload.reason,
            before=before_snapshot,
            after=after_snapshot,
        )

    if not payload.expected_worker_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="expected_worker_id is required unless force=true.",
        )

    if before_info.worker_id != payload.expected_worker_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lock is held by {before_info.worker_id}.",
        )

    db.release_processing_lock(before_info.worker_id)
    after_snapshot = build_lock_snapshot(db.read_processing_lock())
    logger.info(
        f"Processing lock released for {payload.db_type} (worker={before_info.worker_id})."
    )
    return ProcessingLockReleaseResponse(
        db_type=payload.db_type,
        released=True,
        reason=payload.reason,
        before=before_snapshot,
        after=after_snapshot,
    )
