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


from src.infrastructure.persistence.notion.client import NotionDB


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


if __name__ == "__main__":
    unittest.main()
