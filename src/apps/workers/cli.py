"""Simple CLI entry for running the processing worker on demand."""

from __future__ import annotations

import argparse

from src.infrastructure.persistence.factory import DBFactory
from src.services.pipeline.processing_runner import process_pending_tasks


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the background processing worker once.")
    parser.add_argument(
        "--db-type",
        default="sqlite",
        choices=("sqlite", "notion"),
        help="Database backend to drain tasks from.",
    )
    parser.add_argument(
        "--worker-id",
        default=None,
        help="Optional worker identifier for easier lock inspection.",
    )
    args = parser.parse_args()

    db = DBFactory.get_db(args.db_type)
    summary = process_pending_tasks(db=db, worker_id=args.worker_id)
    print(summary.to_dict())


if __name__ == "__main__":
    main()
