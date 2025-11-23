"""Helpers for forming deterministic summary output paths."""

from __future__ import annotations

import os
import time

from src.core.utils.filename import sanitize_filename
from src.core.utils.url import extract_video_id


def build_summary_output_path(
    title: str,
    url: str,
    *,
    now: float | None = None,
    base_dir: str = os.path.join("data", "summaries"),
) -> str:
    """Build a timestamped summary path scoped by video id and sanitized title."""
    ts = time.strftime(
        "%Y%m%d%H%M%S", time.localtime(now) if now is not None else time.localtime()
    )
    video_id = extract_video_id(url) or "noid"
    sanitized_title = sanitize_filename(title or "untitled")
    filename = f"_summarized_{ts}_{video_id}_{sanitized_title}.md"
    return os.path.join(base_dir, filename)
