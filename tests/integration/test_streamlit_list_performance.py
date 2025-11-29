import time

from src.apps.ui.streamlit_app import sort_tasks_for_display, get_notion_display
from tests.fixtures.processing_jobs import build_task


def test_sorting_and_display_performance():
    tasks = [
        build_task(
            id=str(i),
            created_offset_minutes=i % 60,
            notion_page_id="1234-5678" if i % 2 == 0 else None,
            notion_url=None if i % 2 == 0 else "https://www.notion.so/custom",
        )
        for i in range(500)
    ]

    start = time.time()
    sorted_tasks = sort_tasks_for_display(tasks)
    displays = [get_notion_display(task, "https://www.notion.so/workspace") for task in sorted_tasks]
    duration = time.time() - start

    assert duration < 1.0, f"Rendering helpers too slow ({duration:.3f}s)"
    # Ensure outputs align to expected statuses
    assert displays[0]["status"] in {"link", "missing", "invalid"}
