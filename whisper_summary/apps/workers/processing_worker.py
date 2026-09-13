"""Long-running processing worker that polls the persisted task queue."""

from __future__ import annotations

import argparse
import os
import threading
from collections.abc import Callable

from whisper_summary.core.logger import logger
from whisper_summary.infrastructure.repository_composition import create_database
from whisper_summary.services.pipeline.processing_runner import ProcessingSummary, process_pending_tasks


def run_forever(
    *,
    db_type: str = "sqlite",
    worker_id: str = "processing-worker",
    poll_interval_seconds: float = 5.0,
    stop_event: threading.Event | None = None,
    processor: Callable[..., ProcessingSummary] = process_pending_tasks,
) -> None:
    stopper = stop_event or threading.Event()
    db = create_database(db_type)
    logger.info(f"Dedicated processing worker {worker_id} started for {db_type}")
    while not stopper.is_set():
        try:
            processor(db=db, worker_id=worker_id)
        except Exception as exc:  # pragma: no cover - defensive process boundary
            logger.error(f"Processing worker {worker_id} cycle failed: {exc}")
        stopper.wait(max(0.1, poll_interval_seconds))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the dedicated processing worker.")
    parser.add_argument("--db-type", default="sqlite", choices=("sqlite", "notion"))
    parser.add_argument("--worker-id", default="processing-worker")
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=float(os.environ.get("PROCESSING_WORKER_POLL_INTERVAL_SECONDS", "5")),
    )
    args = parser.parse_args()
    run_forever(db_type=args.db_type, worker_id=args.worker_id, poll_interval_seconds=args.poll_interval)


if __name__ == "__main__":
    main()
