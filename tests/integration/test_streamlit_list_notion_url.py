from src.apps.ui.streamlit_app import get_notion_display
from tests.fixtures.processing_jobs import sample_tasks_with_notion


def test_notion_display_variants():
    base = "https://www.notion.so/workspace"
    tasks = sample_tasks_with_notion()
    results = [get_notion_display(task, base) for task in tasks]

    statuses = [item["status"] for item in results]
    assert statuses == ["link", "link", "missing", "invalid"]
    assert results[0]["url"] == "https://www.notion.so/examplepage"
    assert results[2]["message"] in {"尚未同步到 Notion", "Notion 未設定"}
