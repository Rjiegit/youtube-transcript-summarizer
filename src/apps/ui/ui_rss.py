from __future__ import annotations

import sqlite3

from src.core.utils.url import extract_youtube_channel_id, normalize_youtube_feed_url
from src.infrastructure.persistence.sqlite.client import SQLiteDB
from src.infrastructure.persistence.sqlite.rss_subscription_repository import (
    SQLiteRSSSubscriptionRepository,
)
from src.services.rss.channel_monitor import RSSChannelMonitor


def normalize_rss_subscription_input(raw_value: str) -> tuple[str, str]:
    channel_id = extract_youtube_channel_id(raw_value)
    feed_url = normalize_youtube_feed_url(raw_value)
    if not channel_id or not feed_url:
        raise ValueError("請輸入有效的 YouTube channel_id 或 feed URL。")
    return channel_id, feed_url


def add_rss_subscription(
    repository: SQLiteRSSSubscriptionRepository,
    raw_value: str,
    title: str = "",
    enabled: bool = True,
):
    channel_id, feed_url = normalize_rss_subscription_input(raw_value)
    try:
        return repository.add_subscription(
            channel_id=channel_id,
            feed_url=feed_url,
            title=title,
            enabled=enabled,
        )
    except sqlite3.IntegrityError as exc:
        raise ValueError("此 channel 已存在。") from exc


def update_rss_subscription(
    repository: SQLiteRSSSubscriptionRepository,
    subscription_id: str,
    raw_value: str,
    title: str = "",
    enabled: bool = True,
) -> None:
    channel_id, feed_url = normalize_rss_subscription_input(raw_value)
    try:
        repository.update_subscription(
            subscription_id,
            channel_id=channel_id,
            feed_url=feed_url,
            title=title,
            enabled=enabled,
        )
    except sqlite3.IntegrityError as exc:
        raise ValueError("更新後的 channel 與既有訂閱衝突。") from exc


def trigger_rss_poll_once(
    db_path: str,
    monitor_factory=RSSChannelMonitor,
):
    monitor = monitor_factory(
        db=SQLiteDB(db_path=db_path),
        repository=SQLiteRSSSubscriptionRepository(db_path),
    )
    return monitor.poll_once()


def format_rss_poll_results(results) -> list[str]:
    lines: list[str] = []
    for result in results:
        channel_label = getattr(result, "channel_id", "-")
        status = getattr(result, "status", "success")
        if status == "error":
            lines.append(
                f"{channel_label}: error, {getattr(result, 'error', 'unknown error')}"
            )
            continue
        if getattr(result, "seeded", False):
            lines.append(f"{channel_label}: seeded only, no historical videos queued")
            continue
        lines.append(
            f"{channel_label}: new={getattr(result, 'new_tasks', 0)}, "
            f"duplicate={getattr(result, 'duplicates', 0)}"
        )
    return lines
