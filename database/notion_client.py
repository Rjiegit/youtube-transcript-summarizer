import os
from notion_client import Client
from database.database_interface import BaseDB
from typing import List
from database.task import Task
from database.task_adapter import NotionTaskAdapter


class NotionDB(BaseDB):
    """Notion database connector."""

    def __init__(self):
        """Initializes the Notion client."""
        self.notion = Client(auth=os.environ.get("NOTION_API_KEY"))
        self.database_id = os.environ.get("NOTION_DATABASE_ID")
        self.adapter = NotionTaskAdapter()

    def add_task(self, url: str, status: str = "Pending") -> None:
        """Adds a new task to the Notion database."""
        self.notion.pages.create(
            parent={"database_id": self.database_id},
            properties={
                "URL": {"url": url},
                "Name": {"title": [{"text": {"content": url}}]},
                "Status": {"select": {"name": status}},
            },
        )

    def get_pending_tasks(self) -> List[Task]:
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

    def get_all_tasks(self) -> List[Task]:
        """Gets all tasks from the Notion database."""
        response = self.notion.databases.query(database_id=self.database_id)
        results = response.get("results", [])
        return [self.adapter.to_task(item) for item in results]

    def get_task_by_id(self, task_id: str) -> Task:
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
            properties["Name"] = {"title": [{"text": {"content": title}}]}
        if summary:
            properties["Summary"] = {"rich_text": [{"text": {"content": summary}}]}
        if error_message:
            properties["Error Message"] = {
                "rich_text": [{"text": {"content": error_message}}]
            }
        if processing_duration is not None:
            properties["Processing Duration"] = {"number": processing_duration}

        self.notion.pages.update(page_id=task_id, properties=properties)
