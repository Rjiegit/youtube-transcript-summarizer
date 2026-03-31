from __future__ import annotations

import threading
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime

from src.core.config import Config
from src.core.logger import logger
from src.core.time_utils import as_utc, utc_now
from src.core.utils.url import extract_video_id, normalize_youtube_url
from src.domain.rss.models import RSSChannelSubscription, RSSPollResult
from src.infrastructure.persistence.sqlite.rss_subscription_repository import (
    SQLiteRSSSubscriptionRepository,
)
from src.infrastructure.persistence.sqlite.client import SQLiteDB

try:  # pragma: no cover - optional in minimal environments
    import requests
except ModuleNotFoundError:  # pragma: no cover - testing scaffold
    requests = None  # type: ignore


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


@dataclass
class YouTubeFeedEntry:
    video_id: str
    title: str
    url: str
    published_at: datetime
    updated_at: datetime | None = None


@dataclass
class TaskEnqueueResult:
    created: bool
    message: str = ""


class YouTubeRSSFeedClient:
    def fetch_entries(self, feed_url: str) -> list[YouTubeFeedEntry]:
        if requests is None:
            raise RuntimeError("requests is required for RSS monitoring.")
        response = requests.get(feed_url, timeout=15)
        response.raise_for_status()
        return self.parse_entries(response.text)

    def parse_entries(self, xml_text: str) -> list[YouTubeFeedEntry]:
        root = ET.fromstring(xml_text)
        entries: list[YouTubeFeedEntry] = []
        for entry in root.findall("atom:entry", ATOM_NS):
            video_id = (entry.findtext("yt:videoId", default="", namespaces=ATOM_NS) or "").strip()
            title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
            published_raw = (entry.findtext("atom:published", default="", namespaces=ATOM_NS) or "").strip()
            updated_raw = (entry.findtext("atom:updated", default="", namespaces=ATOM_NS) or "").strip()

            link = ""
            for link_node in entry.findall("atom:link", ATOM_NS):
                href = (link_node.attrib.get("href") or "").strip()
                if href:
                    link = href
                    break

            normalized_url = normalize_youtube_url(link) or normalize_youtube_url(
                f"https://www.youtube.com/watch?v={video_id}"
            )
            parsed_video_id = extract_video_id(normalized_url or "")
            if not published_raw or not normalized_url or not parsed_video_id:
                continue

            published_at = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
            updated_at = None
            if updated_raw:
                updated_at = datetime.fromisoformat(updated_raw.replace("Z", "+00:00"))

            entries.append(
                YouTubeFeedEntry(
                    video_id=parsed_video_id,
                    title=title,
                    url=normalized_url,
                    published_at=as_utc(published_at),
                    updated_at=as_utc(updated_at) if updated_at else None,
                )
            )

        entries.sort(key=lambda item: item.published_at)
        return entries


class TaskAPIClient:
    def __init__(self, api_base_url: str, timeout_seconds: int = 15):
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def enqueue_task(self, url: str, channel_id: str) -> TaskEnqueueResult:
        if requests is None:
            raise RuntimeError("requests is required for RSS monitoring.")

        response = requests.post(
            f"{self.api_base_url}/tasks",
            json={
                "url": url,
                "db_type": "sqlite",
                "source_type": "rss",
                "source_channel_id": channel_id,
                "completed_task_policy": "block_existing",
            },
            timeout=self.timeout_seconds,
        )

        detail = ""
        try:
            payload = response.json()
            detail = str(payload.get("detail") or payload.get("message") or "")
        except ValueError:
            detail = (response.text or "").strip()

        if response.status_code == 201:
            return TaskEnqueueResult(created=True, message=detail)
        if response.status_code == 409:
            return TaskEnqueueResult(created=False, message=detail)
        raise RuntimeError(
            f"Task API request failed ({response.status_code}): {detail or 'unknown error'}"
        )


class RSSChannelMonitor:
    def __init__(
        self,
        db: SQLiteDB | None = None,
        repository: SQLiteRSSSubscriptionRepository | None = None,
        feed_client: YouTubeRSSFeedClient | None = None,
        task_client: TaskAPIClient | None = None,
        config: Config | None = None,
    ):
        self.db = db or SQLiteDB()
        self.repository = repository or SQLiteRSSSubscriptionRepository(self.db.db_path)
        self.feed_client = feed_client or YouTubeRSSFeedClient()
        self.config = config or Config()
        self.task_client = task_client or TaskAPIClient(
            api_base_url=self.config.task_api_base_url,
            timeout_seconds=self.config.rss_monitor_task_timeout_seconds,
        )

    def poll_once(self) -> list[RSSPollResult]:
        results: list[RSSPollResult] = []
        for subscription in self.repository.list_subscriptions(enabled_only=True):
            result = self._poll_subscription(subscription)
            results.append(result)
        return results

    def run_forever(self, stop_event: threading.Event | None = None) -> None:
        stopper = stop_event or threading.Event()
        poll_interval = max(
            self.config.rss_monitor_poll_interval_seconds,
            self.config.rss_monitor_min_poll_interval_seconds,
        )
        while not stopper.is_set():
            self.poll_once()
            stopper.wait(poll_interval)

    def _poll_subscription(self, subscription: RSSChannelSubscription) -> RSSPollResult:
        checked_at = utc_now()
        result = RSSPollResult(
            subscription_id=subscription.id,
            channel_id=subscription.channel_id,
        )
        try:
            entries = self.feed_client.fetch_entries(subscription.feed_url)
            newest_published_at = max((entry.published_at for entry in entries), default=None)

            if subscription.last_processed_published_at is None:
                self.repository.update_monitor_state(
                    subscription.id,
                    last_processed_published_at=newest_published_at,
                    last_checked_at=checked_at,
                    last_status="seeded" if newest_published_at else "success",
                    last_error="",
                )
                result.seeded = newest_published_at is not None
                result.status = "seeded" if result.seeded else "success"
                return result

            new_entries = [
                entry
                for entry in entries
                if entry.published_at > as_utc(subscription.last_processed_published_at)
            ]

            for entry in new_entries:
                enqueue_result = self.task_client.enqueue_task(entry.url, subscription.channel_id)
                if enqueue_result.created:
                    result.new_tasks += 1
                else:
                    result.duplicates += 1

            updated_watermark = subscription.last_processed_published_at
            if new_entries:
                updated_watermark = max(entry.published_at for entry in new_entries)

            self.repository.update_monitor_state(
                subscription.id,
                last_processed_published_at=updated_watermark,
                last_checked_at=checked_at,
                last_status="success",
                last_error="",
            )
            return result
        except Exception as exc:
            logger.error(
                f"RSS polling failed for channel {subscription.channel_id}: {exc}"
            )
            result.status = "error"
            result.error = str(exc)
            self.repository.update_monitor_state(
                subscription.id,
                last_processed_published_at=subscription.last_processed_published_at,
                last_checked_at=checked_at,
                last_status="error",
                last_error=str(exc),
            )
            return result
