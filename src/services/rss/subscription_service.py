from __future__ import annotations

from dataclasses import dataclass

from src.core.utils.url import normalize_youtube_feed_url
from src.domain.ports.repositories import RSSSubscriptionRepository
from src.domain.rss.models import RSSSubscriptionConflictError


@dataclass
class RSSSubscriptionCreateResult:
    created: bool
    subscription_id: str | None
    channel_id: str
    feed_url: str
    title: str
    enabled: bool
    message: str


def normalize_rss_subscription_input(raw_value: str) -> tuple[str, str]:
    from src.core.utils.url import extract_youtube_channel_id

    channel_id = extract_youtube_channel_id(raw_value)
    feed_url = normalize_youtube_feed_url(raw_value)
    if not channel_id or not feed_url:
        raise ValueError("請輸入有效的 YouTube channel_id 或 feed URL。")
    return channel_id, feed_url


def create_rss_subscription(
    repository: RSSSubscriptionRepository,
    *,
    channel_id: str,
    feed_url: str | None = None,
    title: str = "",
    enabled: bool = True,
) -> RSSSubscriptionCreateResult:
    normalized_channel_id, normalized_feed_url = normalize_rss_subscription_input(
        feed_url or channel_id
    )
    if normalized_channel_id != channel_id:
        raise ValueError("channel_id 與 feed_url 不一致。")
    normalized_title = (title or "").strip() or normalized_channel_id

    try:
        subscription = repository.add_subscription(
            channel_id=normalized_channel_id,
            feed_url=normalized_feed_url,
            title=normalized_title,
            enabled=enabled,
        )
    except RSSSubscriptionConflictError:
        raise

    return RSSSubscriptionCreateResult(
        created=True,
        subscription_id=subscription.id,
        channel_id=subscription.channel_id,
        feed_url=subscription.feed_url,
        title=subscription.title or normalized_title,
        enabled=subscription.enabled,
        message="RSS subscription created.",
    )


def update_rss_subscription(
    repository: RSSSubscriptionRepository,
    subscription_id: str,
    raw_value: str,
    title: str = "",
    enabled: bool = True,
) -> None:
    channel_id, feed_url = normalize_rss_subscription_input(raw_value)
    normalized_title = (title or "").strip() or channel_id
    try:
        repository.update_subscription(
            subscription_id,
            channel_id=channel_id,
            feed_url=feed_url,
            title=normalized_title,
            enabled=enabled,
        )
    except RSSSubscriptionConflictError:
        raise
