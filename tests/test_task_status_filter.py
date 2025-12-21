import unittest
from types import SimpleNamespace

from src.apps.ui.streamlit_app import collect_task_status_options, filter_tasks_by_status


class TaskStatusFilterTests(unittest.TestCase):
    def test_collect_task_status_options_preserves_order(self):
        tasks = [
            SimpleNamespace(status="Pending"),
            SimpleNamespace(status="Failed"),
            SimpleNamespace(status="Failed Retry Created"),
            SimpleNamespace(status="Pending"),
            SimpleNamespace(status=None),
            SimpleNamespace(status="Completed"),
        ]

        self.assertEqual(
            collect_task_status_options(tasks),
            ["Pending", "Failed", "Failed Retry Created", "Completed"],
        )

    def test_filter_tasks_by_status_handles_none_selection(self):
        tasks = [SimpleNamespace(status="Pending"), SimpleNamespace(status="Failed")]

        self.assertEqual(filter_tasks_by_status(tasks, None), tasks)

    def test_filter_tasks_by_status_handles_empty_selection(self):
        tasks = [SimpleNamespace(status="Pending"), SimpleNamespace(status="Failed")]

        self.assertEqual(filter_tasks_by_status(tasks, []), [])

    def test_filter_tasks_by_status_filters_selected(self):
        tasks = [
            SimpleNamespace(status="Pending"),
            SimpleNamespace(status="Failed"),
            SimpleNamespace(status="Failed Retry Created"),
            SimpleNamespace(status="Completed"),
        ]

        filtered = filter_tasks_by_status(
            tasks,
            ["Failed", "Failed Retry Created", "Completed"],
        )
        self.assertEqual(
            [task.status for task in filtered],
            ["Failed", "Failed Retry Created", "Completed"],
        )


if __name__ == "__main__":
    unittest.main()
