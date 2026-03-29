from __future__ import annotations

from src.infrastructure.persistence.sqlite.client import SQLiteDB
from src.infrastructure.persistence.sqlite.rss_subscription_repository import (
    SQLiteRSSSubscriptionRepository,
)
from src.services.rss.channel_monitor import RSSChannelMonitor
from src.services.rss.subscription_service import (
    create_rss_subscription,
    normalize_rss_subscription_input,
    update_rss_subscription as update_rss_subscription_record,
)


def add_rss_subscription(
    repository: SQLiteRSSSubscriptionRepository,
    raw_value: str,
    title: str = "",
    enabled: bool = True,
):
    channel_id, feed_url = normalize_rss_subscription_input(raw_value)
    return create_rss_subscription(
        repository,
        channel_id=channel_id,
        feed_url=feed_url,
        title=title,
        enabled=enabled,
    )


def update_rss_subscription(
    repository: SQLiteRSSSubscriptionRepository,
    subscription_id: str,
    raw_value: str,
    title: str = "",
    enabled: bool = True,
) -> None:
    update_rss_subscription_record(
        repository,
        subscription_id,
        raw_value,
        title=title,
        enabled=enabled,
    )


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
