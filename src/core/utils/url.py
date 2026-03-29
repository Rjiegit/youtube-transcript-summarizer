"""Utilities for validating and normalizing YouTube URLs and channel feeds."""

from __future__ import annotations
import re
from urllib.parse import parse_qs, urlparse
from typing import Optional

YOUTUBE_PATTERNS = [
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?youtu\.be/([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})"),
    re.compile(r"(?:https?://)?(?:www\.|m\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})"),
]
YOUTUBE_CHANNEL_ID_PATTERN = re.compile(r"^UC[a-zA-Z0-9_-]{22}$")
YOUTUBE_FEED_HOSTS = {"www.youtube.com", "youtube.com"}


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


def is_valid_youtube_channel_id(value: str) -> bool:
    return bool(YOUTUBE_CHANNEL_ID_PATTERN.match((value or "").strip()))


def build_youtube_channel_feed_url(channel_id: str) -> str:
    normalized = (channel_id or "").strip()
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={normalized}"


def extract_youtube_channel_id(value: str) -> Optional[str]:
    candidate = (value or "").strip()
    if not candidate:
        return None
    if is_valid_youtube_channel_id(candidate):
        return candidate

    parsed = urlparse(candidate)
    if parsed.netloc.lower() not in YOUTUBE_FEED_HOSTS or parsed.path != "/feeds/videos.xml":
        return None
    channel_id = parse_qs(parsed.query).get("channel_id", [None])[0]
    if channel_id and is_valid_youtube_channel_id(channel_id):
        return channel_id
    return None


def normalize_youtube_feed_url(value: str) -> Optional[str]:
    channel_id = extract_youtube_channel_id(value)
    if not channel_id:
        return None
    return build_youtube_channel_feed_url(channel_id)
