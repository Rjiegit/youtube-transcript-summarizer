import unittest


class TestAPIModuleStructure(unittest.TestCase):
    def test_feature_routers_are_registered(self) -> None:
        from whisper_summary.apps.api.main import app

        route_paths = {route.path for route in app.routes}
        self.assertTrue(
            {
                "/tasks",
                "/tasks/{task_id}/retry",
                "/rss/subscriptions",
                "/processing-jobs",
                "/processing-lock",
            }.issubset(route_paths)
        )

    def test_api_concerns_live_in_dedicated_modules(self) -> None:
        from whisper_summary.apps.api import dependencies, schemas
        from whisper_summary.apps.api.routers import processing, rss, tasks

        self.assertTrue(hasattr(dependencies, "get_database"))
        self.assertTrue(hasattr(schemas, "TaskCreateRequest"))
        self.assertTrue(hasattr(tasks, "router"))
        self.assertTrue(hasattr(rss, "router"))
        self.assertTrue(hasattr(processing, "router"))


if __name__ == "__main__":
    unittest.main()
