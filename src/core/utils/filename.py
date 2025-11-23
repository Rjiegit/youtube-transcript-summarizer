"""Filename and path helper utilities."""

from __future__ import annotations

import os
import re


def sanitize_filename(filename: str) -> str:
    """Replace characters that are invalid for most filesystems."""
    return re.sub(r'[\\/:*?"<>|]', "_", filename or "")


def truncate_filename(filename: str, max_length: int = 200) -> str:
    """Truncate a filename to the desired byte length while preserving extension."""
    encoded = (filename or "").encode("utf-8")
    if len(encoded) <= max_length:
        return filename

    base_name, ext = os.path.splitext(filename)
    ext_bytes = len(ext.encode("utf-8"))
    available_bytes = max(max_length - ext_bytes, 0)

    truncated_base = base_name
    while len(truncated_base.encode("utf-8")) > available_bytes and truncated_base:
        truncated_base = truncated_base[:-1]

    result = truncated_base + ext
    return result or ext.lstrip(".")
