"""Utilities for validating and normalizing YouTube URLs."""

from __future__ import annotations
import re
from typing import Optional

YOUTUBE_PATTERNS = [
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})"),
]


def extract_video_id(url: str) -> Optional[str]:
    url = (url or "").strip()
    for pat in YOUTUBE_PATTERNS:
        m = pat.search(url)
        if m:
            end_index = m.end(1)
            if end_index < len(url) and re.match(r"[A-Za-z0-9_-]", url[end_index]):
                # ID length exceeds 11 characters; skip this match.
                continue
            return m.group(1)
    return None


def is_valid_youtube_url(url: str) -> bool:
    return extract_video_id(url) is not None


def normalize_youtube_url(url: str) -> Optional[str]:
    vid = extract_video_id(url)
    if not vid:
        return None
    return f"https://www.youtube.com/watch?v={vid}"
