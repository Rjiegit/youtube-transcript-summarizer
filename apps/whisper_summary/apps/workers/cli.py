"""Simple CLI entry for running the processing worker on demand."""

from __future__ import annotations

import argparse

from whisper_summary.apps.workers.processing_worker import (
    build_worker_instance_id,
    create_task_queue,
)
from whisper_summary.services.pipeline.processing_runner import process_pending_tasks


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the background processing worker once.")
    parser.add_argument(
        "--worker-name",
        default="cli",
        help="Human-readable prefix for the generated worker instance ID.",
    )
    args = parser.parse_args()

    db = create_task_queue()
    summary = process_pending_tasks(
        db=db,
        worker_id=build_worker_instance_id(args.worker_name),
    )
    print(summary.to_dict())


if __name__ == "__main__":
    main()
