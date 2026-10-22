import unittest
from unittest.mock import MagicMock, patch

from whisper_summary.infrastructure.storage.summary_storage import SummaryStorage


class SummaryStorageNotionTests(unittest.TestCase):
    def test_summary_chunks_share_a_paragraph_without_inserted_breaks(self):
        storage = SummaryStorage()
        notion = MagicMock()
        notion.pages.create.return_value = {"id": "page-id"}
        text = "# 摘要\n\n*   美食\n    *   " + "食" * 1800 + "\n    *   炸雞"

        with patch.object(storage, "get_notion_env", return_value={
            "notion_client": notion,
            "database_id": "database-id",
        }):
            storage.save_with_notion("title", text, "model", "https://example.com")

        children = notion.pages.create.call_args.kwargs["children"]
        self.assertEqual(len(children), 1)
        rich_text = children[0]["paragraph"]["rich_text"]
        self.assertGreater(len(rich_text), 1)
        self.assertEqual("".join(item["text"]["content"] for item in rich_text), text)
