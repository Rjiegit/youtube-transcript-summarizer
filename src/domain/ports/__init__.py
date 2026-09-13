"""Application-facing ports implemented by infrastructure adapters."""

from src.domain.ports.repositories import RSSSubscriptionRepository, TaskRepository

__all__ = ["RSSSubscriptionRepository", "TaskRepository"]
