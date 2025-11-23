from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from src.domain.tasks.models import Task


@dataclass
class ProcessingLockInfo:
    """Metadata describing the global processing lock."""

    worker_id: str | None
    locked_at: datetime | None


class BaseDB(ABC):
    """Abstract base class for a database interface."""

    @abstractmethod
    def add_task(self, url: str, status: str = "Pending") -> Task:
        """Adds a new task to the database and returns its representation.

        Args:
            url: The URL of the YouTube video.
            status: The initial status of the task.

        Returns:
            The persisted task instance, including the generated identifier.
        """
        raise NotImplementedError

    @abstractmethod
    def get_pending_tasks(self) -> List[Task]:
        """Gets all tasks with a 'Pending' status.

        Returns:
            A list of tasks.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_tasks(self) -> List[Task]:
        """Gets all tasks from the database.

        Returns:
            A list of tasks.
        """
        raise NotImplementedError

    @abstractmethod
    def get_task_by_id(self, task_id: str) -> Task:
        """Gets a single task by its ID.

        Args:
            task_id: The ID of the task to retrieve.

        Returns:
            A single task object.
        """
        raise NotImplementedError

    @abstractmethod
    def acquire_next_task(
        self,
        worker_id: str,
        lock_timeout_seconds: int = 300,
    ) -> Optional[Task]:
        """Atomically picks the next executable task and marks it as processing.

        Args:
            worker_id: Identifier of the worker acquiring the task.
            lock_timeout_seconds: Seconds after which stale locks can be reclaimed.

        Returns:
            The claimed task, or None if no executable task is available.
        """
        raise NotImplementedError

    @abstractmethod
    def acquire_processing_lock(
        self,
        worker_id: str,
        lock_timeout_seconds: int = 300,
    ) -> bool:
        """Attempts to acquire a global processing lock for the worker."""
        raise NotImplementedError

    @abstractmethod
    def refresh_processing_lock(self, worker_id: str) -> None:
        """Extends the lease of the global processing lock."""
        raise NotImplementedError

    @abstractmethod
    def release_processing_lock(self, worker_id: str) -> None:
        """Releases the global processing lock if held by the worker."""
        raise NotImplementedError

    @abstractmethod
    def read_processing_lock(self) -> ProcessingLockInfo:
        """Reads the current state of the processing lock."""
        raise NotImplementedError

    @abstractmethod
    def clear_processing_lock(self) -> None:
        """Unconditionally clears the processing lock."""
        raise NotImplementedError

    @abstractmethod
    def update_task_status(
        self,
        task_id: str,
        status: str,
        title: str = None,
        summary: str = None,
        error_message: str = None,
        processing_duration: Optional[float] = None,
        notion_page_id: Optional[str] = None,
    ) -> None:
        """Updates the status of a task.

        Args:
            task_id: The ID of the task to update.
            status: The new status of the task.
            title: The title of the video.
            summary: The summary of the video.
            error_message: An error message if the task failed.
            processing_duration: Total processing time in seconds.
            notion_page_id: The Notion page identifier created for the summary.
        """
        raise NotImplementedError

    @abstractmethod
    def create_retry_task(
        self,
        source_task: Task,
        retry_reason: Optional[str] = None,
    ) -> Task:
        """Creates a new pending task cloned from a failed task."""
        raise NotImplementedError
