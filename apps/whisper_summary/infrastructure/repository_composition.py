"""Composition helpers for persistence adapters."""

from whisper_summary.infrastructure.persistence.factory import DBFactory
from whisper_summary.infrastructure.persistence.sqlite.rss_subscription_repository import SQLiteRSSSubscriptionRepository


def create_database(db_type: str):
    return DBFactory.get_db(db_type)


def create_rss_repository(db_path: str = "data/tasks.db") -> SQLiteRSSSubscriptionRepository:
    return SQLiteRSSSubscriptionRepository(db_path=db_path)
