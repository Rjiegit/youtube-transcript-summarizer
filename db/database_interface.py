from abc import ABC, abstractmethod
from typing import List
from db.task import Task

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
    def update_task_status(self, task_id: str, status: str, summary: str = None, error_message: str = None) -> None:
        """Updates the status of a task.

        Args:
            task_id: The ID of the task to update.
            status: The new status of the task.
            summary: The summary of the video.
            error_message: An error message if the task failed.
        """
        pass
