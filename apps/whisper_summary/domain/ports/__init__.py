"""Application-facing ports implemented by infrastructure adapters."""

from whisper_summary.domain.ports.repositories import RSSSubscriptionRepository, TaskRepository

__all__ = ["RSSSubscriptionRepository", "TaskRepository"]
