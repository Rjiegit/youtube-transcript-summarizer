import os
from typing import Optional

from notion_client import Client

from database.database_interface import BaseDB
from database.task import Task
from database.task_adapter import NotionTaskAdapter
from database.notion_utils import build_rich_text_array


class NotionDB(BaseDB):
    """Notion database connector."""

    def __init__(self):
        """Initializes the Notion client."""
        self.notion = Client(auth=os.environ.get("NOTION_API_KEY"))
        self.database_id = os.environ.get("NOTION_DATABASE_ID")
        self.adapter = NotionTaskAdapter()

    def add_task(self, url: str, status: str = "Pending") -> None:
        """Adds a new task to the Notion database."""
        name_text = build_rich_text_array(url or "") or [
            {"type": "text", "text": {"content": url or ""}}
        ]

        self.notion.pages.create(
            parent={"database_id": self.database_id},
            properties={
                "URL": {"url": url},
                "Name": {"title": name_text},
                "Status": {"select": {"name": status}},
            },
        )

    def get_pending_tasks(self) -> list[Task]:
        """Gets all tasks with a 'Pending' status from the Notion database."""
        response = self.notion.databases.query(
            database_id=self.database_id,
            filter={
                "property": "Status",
                "select": {"equals": "Pending"},
            },
        )
        results = response.get("results", [])
        return [self.adapter.to_task(item) for item in results]

    def get_all_tasks(self) -> list[Task]:
        """Gets all tasks from the Notion database."""
        response = self.notion.databases.query(database_id=self.database_id)
        results = response.get("results", [])
        return [self.adapter.to_task(item) for item in results]

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Gets a single task by its ID from the Notion database."""
        response = self.notion.pages.retrieve(page_id=task_id)
        return self.adapter.to_task(response)

    def update_task_status(
        self,
        task_id: str,
        status: str,
        title: str = None,
        summary: str = None,
        error_message: str = None,
        processing_duration: float = None,
    ) -> None:
        """Updates the status of a task in the Notion database."""
        properties = {"Status": {"select": {"name": status}}}
        if title:
            properties["Name"] = {"title": build_rich_text_array(title)}
        if summary:
            properties["Summary"] = {"rich_text": build_rich_text_array(summary)}
        if error_message:
            properties["Error Message"] = {
                "rich_text": build_rich_text_array(error_message)
            }
        if processing_duration is not None:
            properties["Processing Duration"] = {"number": processing_duration}

        self.notion.pages.update(page_id=task_id, properties=properties)

    def create_retry_task(
        self, source_task: Task, retry_reason: Optional[str] = None
    ) -> Task:
        """Creates a new pending task cloned from a failed Notion task."""
        reason = retry_reason or source_task.error_message or "Manual retry"
        name_value = source_task.title or source_task.url or ""
        properties = {
            "URL": {"url": source_task.url},
            "Name": {"title": build_rich_text_array(name_value)},
            "Status": {"select": {"name": "Pending"}},
        }
        if reason:
            properties["Retry Reason"] = {
                "rich_text": build_rich_text_array(reason)
            }
        if source_task.id:
            properties["Retry Of"] = {"relation": [{"id": source_task.id}]}

        response = self.notion.pages.create(
            parent={"database_id": self.database_id},
            properties=properties,
        )
        return self.adapter.to_task(response)
