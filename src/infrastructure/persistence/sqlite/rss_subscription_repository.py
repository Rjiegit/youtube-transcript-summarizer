from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from src.domain.rss.models import RSSChannelSubscription


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class SQLiteRSSSubscriptionRepository:
    def __init__(self, db_path: str = "data/tasks.db"):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _to_model(self, row: sqlite3.Row) -> RSSChannelSubscription:
        return RSSChannelSubscription(
            id=str(row["id"]),
            channel_id=row["channel_id"],
            feed_url=row["feed_url"],
            title=row["title"] or "",
            enabled=bool(row["enabled"]),
            last_processed_published_at=_parse_datetime(row["last_processed_published_at"]),
            last_checked_at=_parse_datetime(row["last_checked_at"]),
            last_status=row["last_status"] or "",
            last_error=row["last_error"] or "",
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )

    def list_subscriptions(self, enabled_only: bool = False) -> list[RSSChannelSubscription]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if enabled_only:
                rows = cursor.execute(
                    """
                    SELECT * FROM rss_channel_subscriptions
                    WHERE enabled = 1
                    ORDER BY created_at ASC, id ASC
                    """
                ).fetchall()
            else:
                rows = cursor.execute(
                    """
                    SELECT * FROM rss_channel_subscriptions
                    ORDER BY created_at ASC, id ASC
                    """
                ).fetchall()
        finally:
            conn.close()
        return [self._to_model(row) for row in rows]

    def get_subscription(self, subscription_id: str) -> Optional[RSSChannelSubscription]:
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM rss_channel_subscriptions WHERE id = ?",
                (subscription_id,),
            ).fetchone()
        finally:
            conn.close()
        return self._to_model(row) if row else None

    def add_subscription(
        self,
        channel_id: str,
        feed_url: str,
        title: str = "",
        enabled: bool = True,
    ) -> RSSChannelSubscription:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO rss_channel_subscriptions (channel_id, feed_url, title, enabled)
                VALUES (?, ?, ?, ?)
                """,
                (channel_id, feed_url, title or "", 1 if enabled else 0),
            )
            subscription_id = str(cursor.lastrowid)
            conn.commit()
        finally:
            conn.close()
        subscription = self.get_subscription(subscription_id)
        if subscription is None:  # pragma: no cover - defensive guard
            raise RuntimeError("Failed to load RSS subscription after insert.")
        return subscription

    def update_subscription(
        self,
        subscription_id: str,
        *,
        channel_id: str,
        feed_url: str,
        title: str,
        enabled: bool,
    ) -> None:
        conn = self._get_connection()
        try:
            conn.execute(
                """
                UPDATE rss_channel_subscriptions
                SET channel_id = ?,
                    feed_url = ?,
                    title = ?,
                    enabled = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (channel_id, feed_url, title or "", 1 if enabled else 0, subscription_id),
            )
            conn.commit()
        finally:
            conn.close()

    def set_enabled(self, subscription_id: str, enabled: bool) -> None:
        conn = self._get_connection()
        try:
            conn.execute(
                """
                UPDATE rss_channel_subscriptions
                SET enabled = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (1 if enabled else 0, subscription_id),
            )
            conn.commit()
        finally:
            conn.close()

    def delete_subscription(self, subscription_id: str) -> None:
        conn = self._get_connection()
        try:
            conn.execute(
                "DELETE FROM rss_channel_subscriptions WHERE id = ?",
                (subscription_id,),
            )
            conn.commit()
        finally:
            conn.close()

    def update_monitor_state(
        self,
        subscription_id: str,
        *,
        last_processed_published_at: datetime | None = None,
        last_checked_at: datetime | None = None,
        last_status: str = "",
        last_error: str = "",
    ) -> None:
        conn = self._get_connection()
        try:
            conn.execute(
                """
                UPDATE rss_channel_subscriptions
                SET last_processed_published_at = ?,
                    last_checked_at = ?,
                    last_status = ?,
                    last_error = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    last_processed_published_at.isoformat() if last_processed_published_at else None,
                    last_checked_at.isoformat() if last_checked_at else None,
                    last_status,
                    last_error,
                    subscription_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()
