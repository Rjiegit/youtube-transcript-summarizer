import json
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.infrastructure.persistence.notion.client import NotionDB


class TestNotionCompletedPageContract(unittest.TestCase):
    def test_python_writer_matches_shared_completed_page_fixture(self) -> None:
        fixture_path = Path(__file__).parents[1] / "fixtures" / "notion_completed_page.json"
        expected = json.loads(fixture_path.read_text(encoding="utf-8"))["properties"]
        notion = MagicMock()

        with patch.dict(os.environ, {"NOTION_API_KEY": "token", "NOTION_DATABASE_ID": "database-id"}):
            db = NotionDB()
            db.notion = notion
            db.update_task_status(
                "contract-page-id",
                "Completed",
                title="Contract title",
                summary="Contract summary",
                processing_duration=12.5,
            )

        properties = notion.pages.update.call_args.kwargs["properties"]
        self.assertEqual(properties["Status"], expected["Status"])
        self.assertEqual(properties["Processing Duration"], expected["Processing Duration"])
        self.assertEqual(set(properties), {"Status", "Name", "Summary", "Processing Duration"})
