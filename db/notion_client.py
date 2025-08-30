import os
from notion_client import Client
from database_interface import BaseDB
from typing import List, Dict, Any

class NotionDB(BaseDB):
    """Notion database connector."""

    def __init__(self):
        """Initializes the Notion client."""
        self.notion = Client(auth=os.environ.get("NOTION_API_KEY"))
        self.database_id = os.environ.get("NOTION_DATABASE_ID")

    def add_task(self, url: str, status: str = "Pending") -> None:
        """Adds a new task to the Notion database."""
        self.notion.pages.create(
            parent={"database_id": self.database_id},
            properties={
                "URL": {"url": url},
                "Status": {"select": {"name": status}},
            },
        )

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Gets all tasks with a 'Pending' status from the Notion database."""
        response = self.notion.databases.query(
            database_id=self.database_id,
            filter={
                "property": "Status",
                "select": {"equals": "Pending"},
            },
        )
        return response.get("results", [])

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Gets all tasks from the Notion database."""
        response = self.notion.databases.query(database_id=self.database_id)
        return response.get("results", [])

    def update_task_status(self, task_id: str, status: str, summary: str = None, error_message: str = None) -> None:
        """Updates the status of a task in the Notion database."""
        properties = {"Status": {"select": {"name": status}}}
        if summary:
            properties["Summary"] = {"rich_text": [{"text": {"content": summary}}]}
        if error_message:
            properties["Error Message"] = {"rich_text": [{"text": {"content": error_message}}]}

        self.notion.pages.update(page_id=task_id, properties=properties)
