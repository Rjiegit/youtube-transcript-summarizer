from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


class TestRuntimeEntrypoints(unittest.TestCase):
    def test_runtime_configuration_has_no_legacy_src_entrypoints(self) -> None:
        for relative_path in ("compose.yaml", "Makefile"):
            content = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
            with self.subTest(path=relative_path):
                self.assertNotIn("src.apps", content)
                self.assertNotIn("src/apps", content)

    def test_compose_disables_runtime_dependency_sync(self) -> None:
        content = (REPOSITORY_ROOT / "compose.yaml").read_text(encoding="utf-8")

        self.assertIn('UV_FROZEN: "1"', content)
        self.assertIn('UV_NO_SYNC: "1"', content)
        self.assertIn("./apps/whisper_summary/.env", content)

    def test_make_run_uses_current_worker_cli_arguments(self) -> None:
        content = (REPOSITORY_ROOT / "Makefile").read_text(encoding="utf-8")

        self.assertIn(
            "uv run --env-file $(PYTHON_PROJECT_DIR)/.env python -m whisper_summary.apps.workers.cli",
            content,
        )
        self.assertIn("export UV_PROJECT := $(CURDIR)/$(PYTHON_PROJECT_DIR)", content)
        self.assertNotIn("apps.workers.cli --db-type", content)


if __name__ == "__main__":
    unittest.main()
