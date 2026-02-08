from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return a timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def utc_now_naive() -> datetime:
    """Return a naive datetime representing the current UTC time.

    Useful when persisting timestamps as strings without timezone offsets while
    still avoiding deprecated `datetime.utcnow()`.
    """
    return utc_now().replace(tzinfo=None)


def as_utc(value: datetime) -> datetime:
    """Normalize a datetime to timezone-aware UTC.

    - Naive datetimes are treated as UTC.
    - Aware datetimes are converted to UTC.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

