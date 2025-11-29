from src.apps.ui.streamlit_app import sort_tasks_for_display
from tests.fixtures.processing_jobs import sample_tasks_for_sorting, build_task


def test_sorting_preserves_desc_created_at():
    tasks = sample_tasks_for_sorting()
    sorted_tasks = sort_tasks_for_display(tasks)
    assert [task.id for task in sorted_tasks] == ["10", "11", "12"]


def test_sorting_handles_missing_created_at():
    tasks = sample_tasks_for_sorting()
    tasks.append(build_task(id="no-date", created_offset_minutes=0, title="No date"))
    tasks[-1].created_at = None
    sorted_tasks = sort_tasks_for_display(tasks)
    assert sorted_tasks[-1].id == "no-date"
