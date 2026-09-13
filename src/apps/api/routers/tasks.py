"""Task creation and retry endpoints."""

import os

from fastapi import APIRouter, HTTPException, Response, status

from src.apps.api.dependencies import ensure_db_configuration, get_database, schedule_job
from src.apps.api.schemas import TaskCreateRequest, TaskCreateResponse, TaskRetryRequest, TaskRetryResponse
from src.core.logger import logger
from src.core.utils.url import is_valid_youtube_url, normalize_youtube_url
from src.services.tasks.processing_scheduler import SchedulingResult
from src.services.tasks.task_creation import create_task_record

FAILED_RETRY_CREATED_STATUS = "Failed Retry Created"
TASK_CACHE_TTL_SECONDS = int(os.environ.get("TASK_CACHE_TTL_SECONDS", "3600"))
router = APIRouter()


@router.post("/tasks", response_model=TaskCreateResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreateRequest, response: Response):
    """Create a new task and persist it in the selected backend.

    Deduplication rules (based on normalised URL):
    * **Completed within TTL** → 200 with cached result.
    * **Pending / Processing** → 409 Conflict.
    * Otherwise → 201 new task.
    """

    normalized_url = normalize_youtube_url(payload.url)
    if not normalized_url or not is_valid_youtube_url(normalized_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid YouTube URL.",
        )

    ensure_db_configuration(payload.db_type)
    db = get_database(payload.db_type)

    try:
        creation = create_task_record(
            db=db,
            url=normalized_url,
            source_type=payload.source_type,
            source_channel_id=payload.source_channel_id,
            cache_ttl_seconds=TASK_CACHE_TTL_SECONDS,
            completed_task_policy=payload.completed_task_policy,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task.",
        ) from exc

    if creation.outcome in {"duplicate_active", "duplicate_completed"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=creation.message,
        )

    if creation.cached and creation.task is not None:
        response.status_code = status.HTTP_200_OK
        return TaskCreateResponse(
            task_id=str(creation.task.id),
            status=creation.task.status,
            db_type=payload.db_type,
            message=creation.message,
            processing_started=False,
            processing_worker_id=None,
            cached=True,
        )

    task = creation.task
    if task is None:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task creation returned no task.",
        )

    try:
        scheduling_result = schedule_job(
            db_type=payload.db_type,
            db=db,
        )
    except HTTPException as exc:
        logger.error(
            f"Failed to schedule processing worker after task creation: {exc.detail}"
        )
        scheduling_result = SchedulingResult(
            accepted=False,
            worker_id=None,
            message=str(exc.detail) if exc.detail else "Failed to schedule processing worker.",
        )
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.error(
            f"Failed to schedule processing worker after task creation: {exc}"
        )
        scheduling_result = SchedulingResult(
            accepted=False,
            worker_id=None,
            message="Task queued, but failed to schedule processing worker.",
        )

    message = creation.message
    if scheduling_result.accepted:
        worker_note = (
            f" Processing worker scheduled (worker: {scheduling_result.worker_id})."
        )
        message += worker_note
    else:
        message += f" {scheduling_result.message}"

    return TaskCreateResponse(
        task_id=str(task.id),
        status=task.status,
        db_type=payload.db_type,
        message=message,
        processing_started=scheduling_result.accepted,
        processing_worker_id=scheduling_result.worker_id,
        cached=False,
    )




@router.post(
    "/tasks/{task_id}/retry",
    response_model=TaskRetryResponse,
    status_code=status.HTTP_201_CREATED,
)
def retry_task(task_id: str, payload: TaskRetryRequest) -> TaskRetryResponse:
    """Create a retry task from a failed task."""

    ensure_db_configuration(payload.db_type)
    db = get_database(payload.db_type)

    source_task = db.get_task_by_id(task_id)
    if not source_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    if source_task.status != "Failed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task status must be Failed to retry.",
        )

    try:
        new_task = db.create_retry_task(source_task, payload.retry_reason)
        db.update_task_status(source_task.id, FAILED_RETRY_CREATED_STATUS)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create retry task.",
        ) from exc

    return TaskRetryResponse(
        task_id=str(new_task.id),
        source_task_id=str(source_task.id),
        status=new_task.status,
        db_type=payload.db_type,
        message="Retry task created.",
    )



