from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RSSChannelSubscription:
    id: str
    channel_id: str
    feed_url: str
    title: str = ""
    enabled: bool = True
    last_processed_published_at: Optional[datetime] = None
    last_checked_at: Optional[datetime] = None
    last_status: str = ""
    last_error: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class RSSPollResult:
    subscription_id: str
    channel_id: str
    new_tasks: int = 0
    duplicates: int = 0
    seeded: bool = False
    status: str = "success"
    error: str = ""
