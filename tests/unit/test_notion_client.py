import sys
import types
import unittest
from unittest.mock import MagicMock, patch


if "notion_client" not in sys.modules:  # pragma: no cover - testing scaffold
    notion_stub = types.ModuleType("notion_client")

    class _Client:
        def __init__(self, *_, **__):
            pass

    notion_stub.Client = _Client
    sys.modules["notion_client"] = notion_stub


from whisper_summary.infrastructure.persistence.notion.client import NotionDB
from whisper_summary.infrastructure.persistence.sqlite.task_adapter import NotionTaskAdapter


class NotionClientTests(unittest.TestCase):
    def test_get_all_tasks_queries_latest_100_by_created_time(self) -> None:
        mock_notion = MagicMock()
        mock_notion.databases.query.return_value = {"results": []}

        with patch.dict(
            "os.environ",
            {"NOTION_API_KEY": "token", "NOTION_DATABASE_ID": "database-id"},
        ):
            db = NotionDB()
            db.notion = mock_notion

            tasks = db.get_all_tasks()

        self.assertEqual(tasks, [])
        mock_notion.databases.query.assert_called_once_with(
            database_id="database-id",
            sorts=[{"timestamp": "created_time", "direction": "descending"}],
            page_size=100,
        )

    def test_add_task_writes_processing_engine_override(self) -> None:
        mock_notion = MagicMock()
        mock_notion.pages.create.return_value = {
            "id": "page-id",
            "created_time": "2026-09-20T00:00:00+00:00",
            "properties": {
                "URL": {"url": "https://youtu.be/example"},
                "Name": {"title": []},
                "Status": {"select": {"name": "Pending"}},
                "Processing Engine": {"select": {"name": "LangGraph"}},
            },
        }

        with patch.dict(
            "os.environ",
            {"NOTION_API_KEY": "token", "NOTION_DATABASE_ID": "database-id"},
        ):
            db = NotionDB()
            db.notion = mock_notion
            task = db.add_task(
                "https://youtu.be/example",
                processing_engine="langgraph",
            )

        properties = mock_notion.pages.create.call_args.kwargs["properties"]
        self.assertEqual(
            properties["Processing Engine"],
            {"select": {"name": "LangGraph"}},
        )
        self.assertEqual(task.processing_engine, "langgraph")

    def test_adapter_treats_missing_processing_engine_as_default(self) -> None:
        task = NotionTaskAdapter().to_task(
            {
                "id": "page-id",
                "created_time": "2026-09-20T00:00:00+00:00",
                "properties": {
                    "URL": {"url": "https://youtu.be/example"},
                    "Name": {"title": []},
                    "Status": {"select": {"name": "Pending"}},
                },
            }
        )

        self.assertIsNone(task.processing_engine)


if __name__ == "__main__":
    unittest.main()
