import os
from unittest import TestCase

from src.apps.ui.streamlit_app import build_notion_url, get_notion_display
from tests.fixtures.processing_jobs import build_task


class TestStreamlitNotionUrl(TestCase):
    def setUp(self) -> None:
        self.notion_base = "https://www.notion.so/workspace"

    def test_build_notion_url_prefers_existing(self):
        url = build_notion_url(
            notion_base_url=self.notion_base,
            notion_page_id="1234-5678",
            existing_url="https://www.notion.so/custom",
        )
        self.assertEqual(url, "https://www.notion.so/custom")

    def test_build_notion_url_from_page_id(self):
        url = build_notion_url(
            notion_base_url=self.notion_base,
            notion_page_id="1234-5678",
            existing_url=None,
        )
        self.assertEqual(url, "https://www.notion.so/workspace/12345678")

    def test_get_notion_display_link(self):
        task = build_task(id="1", notion_url="https://www.notion.so/custom-link")
        display = get_notion_display(task, self.notion_base)
        self.assertEqual(display["status"], "link")
        self.assertEqual(display["url"], "https://www.notion.so/custom-link")

    def test_get_notion_display_invalid(self):
        task = build_task(id="2", notion_url="ftp://invalid")
        display = get_notion_display(task, self.notion_base)
        self.assertEqual(display["status"], "invalid")

    def test_get_notion_display_missing_when_no_base(self):
        task = build_task(id="3", notion_url=None, notion_page_id=None)
        display = get_notion_display(task, None)
        self.assertEqual(display["status"], "missing")
        self.assertEqual(display["message"], "Notion 未設定")
