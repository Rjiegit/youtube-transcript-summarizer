import unittest
from unittest.mock import patch, MagicMock
import os

# Set dummy environment variables for testing
os.environ["NOTION_API_KEY"] = "test_api_key"
os.environ["NOTION_DATABASE_ID"] = "test_db_id"

from db import NotionDB


class TestNotionDB(unittest.TestCase):
    @patch("db.notion_client.Client")
    def setUp(self, MockClient):
        self.mock_notion = MockClient.return_value
        self.db = NotionDB()

    def test_add_task(self):
        """Test adding a task to Notion."""
        url = "https://www.youtube.com/watch?v=test"
        self.db.add_task(url)

        self.mock_notion.pages.create.assert_called_once_with(
            parent={"database_id": "test_db_id"},
            properties={
                "URL": {"url": url},
                "Status": {"select": {"name": "Pending"}},
            },
        )

    def test_get_pending_tasks(self):
        """Test getting pending tasks from Notion."""
        mock_response = {"results": [{"id": "task1"}, {"id": "task2"}]}
        self.mock_notion.databases.query.return_value = mock_response

        tasks = self.db.get_pending_tasks()

        self.mock_notion.databases.query.assert_called_once_with(
            database_id="test_db_id",
            filter={
                "property": "Status",
                "select": {"equals": "Pending"},
            },
        )
        self.assertEqual(tasks, mock_response["results"])

    def test_update_task_status_completed(self):
        """Test updating a task status to Completed."""
        task_id = "test_task_id"
        summary = "This is a summary."
        self.db.update_task_status(task_id, "Completed", summary=summary)

        self.mock_notion.pages.update.assert_called_once_with(
            page_id=task_id,
            properties={
                "Status": {"select": {"name": "Completed"}},
                "Summary": {"rich_text": [{"text": {"content": summary}}]},
            },
        )

    def test_update_task_status_failed(self):
        """Test updating a task status to Failed."""
        task_id = "test_task_id"
        error_message = "This is an error message."
        self.db.update_task_status(task_id, "Failed", error_message=error_message)

        self.mock_notion.pages.update.assert_called_once_with(
            page_id=task_id,
            properties={
                "Status": {"select": {"name": "Failed"}},
                "Error Message": {"rich_text": [{"text": {"content": error_message}}]},
            },
        )


if __name__ == "__main__":
    unittest.main()
