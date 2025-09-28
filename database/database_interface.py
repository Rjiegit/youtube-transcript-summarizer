from abc import ABC, abstractmethod
from typing import List, Optional

from database.task import Task


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
    def update_task_status(
        self,
        task_id: str,
        status: str,
        title: str = None,
        summary: str = None,
        error_message: str = None,
        processing_duration: Optional[float] = None,
    ) -> None:
        """Updates the status of a task.

        Args:
            task_id: The ID of the task to update.
            status: The new status of the task.
            title: The title of the video.
            summary: The summary of the video.
            error_message: An error message if the task failed.
            processing_duration: Total processing time in seconds.
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
