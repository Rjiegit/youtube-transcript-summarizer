from abc import ABC, abstractmethod
from typing import List
from database.task import Task


class BaseDB(ABC):
    """Abstract base class for a database interface."""

    @abstractmethod
    def add_task(self, url: str, status: str = "Pending") -> None:
        """Adds a new task to the database.

        Args:
            url: The URL of the YouTube video.
            status: The initial status of the task.
        """
        pass

    @abstractmethod
    def get_pending_tasks(self) -> List[Task]:
        """Gets all tasks with a 'Pending' status.

        Returns:
            A list of tasks.
        """
        pass

    @abstractmethod
    def get_all_tasks(self) -> List[Task]:
        """Gets all tasks from the database.

        Returns:
            A list of tasks.
        """
        pass

    @abstractmethod
    def get_task_by_id(self, task_id: str) -> Task:
        """Gets a single task by its ID.

        Args:
            task_id: The ID of the task to retrieve.

        Returns:
            A single task object.
        """
        pass

    @abstractmethod
    def update_task_status(
        self,
        task_id: str,
        status: str,
        title: str = None,
        summary: str = None,
        error_message: str = None,
        processing_duration: float | None = None,
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
        pass
