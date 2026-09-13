"""Compatibility result type for processing scheduling API responses.

Processing execution now belongs to ``src.apps.workers.processing_worker``.
"""

from dataclasses import dataclass


@dataclass
class SchedulingResult:
    accepted: bool
    worker_id: str | None
    message: str
