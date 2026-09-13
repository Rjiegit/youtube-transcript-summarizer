"""Repository protocols used by application services."""

from datetime import datetime
from typing import Protocol

from whisper_summary.domain.rss.models import RSSChannelSubscription
from whisper_summary.domain.tasks.models import Task


class TaskRepository(Protocol):
    def find_recent_task_by_url(self, url: str) -> Task | None: ...

    def add_task(
        self,
        url: str,
        *,
        source_type: str = "manual",
        source_channel_id: str | None = None,
    ) -> Task: ...


class RSSSubscriptionRepository(Protocol):
    def list_subscriptions(self, enabled_only: bool = False) -> list[RSSChannelSubscription]: ...

    def add_subscription(
        self,
        channel_id: str,
        feed_url: str,
        title: str = "",
        enabled: bool = True,
    ) -> RSSChannelSubscription: ...

    def update_subscription(
        self,
        subscription_id: str,
        *,
        channel_id: str,
        feed_url: str,
        title: str,
        enabled: bool,
    ) -> None: ...

    def set_enabled(self, subscription_id: str, enabled: bool) -> None: ...

    def delete_subscription(self, subscription_id: str) -> None: ...

    def update_monitor_state(
        self,
        subscription_id: str,
        *,
        last_processed_published_at: datetime | None = None,
        last_checked_at: datetime | None = None,
        last_status: str = "",
        last_error: str = "",
    ) -> None: ...
