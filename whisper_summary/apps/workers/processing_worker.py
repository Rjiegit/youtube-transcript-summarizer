"""Long-running processing worker that polls the persisted task queue."""

from __future__ import annotations

import argparse
import os
import socket
import threading
import uuid
from collections.abc import Callable

from whisper_summary.core.logger import logger
from whisper_summary.infrastructure.llm.summarizer_service import (
    log_codex_cli_startup_status,
)
from whisper_summary.infrastructure.task_queue.http_client import HttpTaskQueue
from whisper_summary.services.pipeline.processing_runner import (
    TASK_LEASE_HEARTBEAT_SECONDS,
    ProcessingSummary,
    process_pending_tasks,
)


DEFAULT_POLL_INTERVAL_SECONDS = 60.0


def create_task_queue() -> HttpTaskQueue:
    worker_token = os.getenv("PROCESSING_WORKER_TOKEN") or os.getenv(
        "PROCESSING_LOCK_ADMIN_TOKEN", ""
    )
    return HttpTaskQueue(
        os.getenv("TASK_API_BASE_URL", "http://localhost:8080"),
        worker_token,
    )


def build_worker_instance_id(worker_name: str) -> str:
    return (
        f"{worker_name}:{socket.gethostname()}:{os.getpid()}:"
        f"{uuid.uuid4().hex[:8]}"
    )


def run_forever(
    *,
    worker_id: str = "processing-worker",
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    stop_event: threading.Event | None = None,
    processor: Callable[..., ProcessingSummary] = process_pending_tasks,
) -> None:
    stopper = stop_event or threading.Event()
    log_codex_cli_startup_status()
    db = create_task_queue()
    logger.info(
        f"Dedicated processing worker {worker_id} started "
        f"with queue={db.base_url} "
        f"heartbeat={TASK_LEASE_HEARTBEAT_SECONDS}s"
    )
    while not stopper.is_set():
        try:
            processor(db=db, worker_id=worker_id)
        except Exception as exc:  # pragma: no cover - defensive process boundary
            logger.exception(
                f"Processing worker {worker_id} cycle failed "
                f"({type(exc).__name__}): {exc!r}"
            )
        stopper.wait(max(0.1, poll_interval_seconds))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the dedicated processing worker.")
    parser.add_argument(
        "--worker-name",
        default=os.environ.get("PROCESSING_WORKER_NAME", "processing-worker"),
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=float(
            os.environ.get(
                "PROCESSING_WORKER_POLL_INTERVAL_SECONDS",
                str(DEFAULT_POLL_INTERVAL_SECONDS),
            )
        ),
    )
    args = parser.parse_args()
    run_forever(
        worker_id=build_worker_instance_id(args.worker_name),
        poll_interval_seconds=args.poll_interval,
    )


if __name__ == "__main__":
    main()
