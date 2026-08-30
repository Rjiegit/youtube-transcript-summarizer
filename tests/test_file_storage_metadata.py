import json
import os
import tempfile
import unittest

from src.infrastructure.storage.file_storage import FileManager


class TestFileManagerMetadata(unittest.TestCase):
    def test_save_json_preserves_unicode_and_writes_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "影片.metadata.json")
            result = FileManager.save_json(
                {"description": "第一行\n第二行", "schema_version": 1},
                output_file,
            )

            with open(result["path"], encoding="utf-8") as saved_file:
                content = saved_file.read()

        self.assertIn("影片.metadata.json", result["path"])
        self.assertIn("第一行", content)
        self.assertEqual(
            json.loads(content),
            {"description": "第一行\n第二行", "schema_version": 1},
        )

    def test_json_sidecar_keeps_actual_summary_stem_for_long_title(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            requested_summary = os.path.join(
                tmpdir,
                f"{'很長的影片標題' * 20}.md",
            )
            summary_result = FileManager.save_text("summary", requested_summary)
            summary_path = summary_result["path"]
            requested_sidecar = (
                os.path.splitext(summary_path)[0] + ".metadata.json"
            )

            sidecar_result = FileManager.save_json({}, requested_sidecar)

        summary_stem = os.path.splitext(os.path.basename(summary_path))[0]
        sidecar_name = os.path.basename(sidecar_result["path"])
        self.assertEqual(sidecar_name, f"{summary_stem}.metadata.json")


if __name__ == "__main__":
    unittest.main()
