"""Processing job and lock administration endpoints."""

import os

from fastapi import APIRouter, Header, HTTPException, status

from whisper_summary.apps.api.dependencies import ensure_db_configuration, get_database
from whisper_summary.apps.api.schemas import (
    ProcessingJobCreateRequest,
    ProcessingJobCreateResponse,
    ProcessingLockReleaseRequest,
    ProcessingLockReleaseResponse,
    ProcessingLockSnapshot,
    ProcessingLockStatusResponse,
    normalize_db_type,
)
from whisper_summary.core.logger import logger
from whisper_summary.core.time_utils import as_utc, utc_now
from whisper_summary.domain.interfaces.database import ProcessingLockInfo
from whisper_summary.services.pipeline.processing_runner import PROCESSING_LOCK_TIMEOUT_SECONDS

router = APIRouter()


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
