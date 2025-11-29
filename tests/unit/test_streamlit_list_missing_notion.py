from src.apps.ui.streamlit_app import get_notion_display
from tests.fixtures.processing_jobs import build_task


def test_missing_notion_with_base():
    task = build_task(id="missing", notion_page_id=None, notion_url=None)
    display = get_notion_display(task, "https://www.notion.so/workspace")
    assert display["status"] == "missing"
    assert "Notion" in display["message"]


def test_missing_notion_without_base():
    task = build_task(id="missing", notion_page_id=None, notion_url=None)
    display = get_notion_display(task, None)
    assert display["status"] == "missing"
    assert display["message"] == "Notion 未設定"
