import os
import time
import unittest

from src.services.outputs.path_builder import build_summary_output_path


class TestBuildSummaryOutputPath(unittest.TestCase):
    def test_path_contains_timestamp_id_title(self):
        title = "我的/影片:標題?*"
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        fixed_time = 1735689600  # fixed epoch seconds
        path = build_summary_output_path(title, url, now=fixed_time)

        self.assertTrue(path.startswith(os.path.join("data", "summaries")))
        filename = os.path.basename(path)
        self.assertTrue(filename.startswith("_summarized_"))
        self.assertIn("dQw4w9WgXcQ", filename)
        # sanitized characters should be replaced by underscore
        self.assertNotIn("/", filename)
        self.assertNotIn(":", filename)
        self.assertNotIn("?", filename)
        self.assertNotIn("*", filename)
        self.assertTrue(filename.endswith(".md"))

        # timestamp formatted as YYYYMMDDHHMMSS for fixed_time (localtime)
        expected_ts = time.strftime("%Y%m%d%H%M%S", time.localtime(fixed_time))
        self.assertIn(expected_ts, filename)

    def test_uniqueness_with_different_timestamps(self):
        title = "測試"
        url = "https://youtu.be/dQw4w9WgXcQ"
        t1 = 1735689600  # 2025-01-01 00:00:00
        t2 = 1735689601  # +1 sec
        p1 = build_summary_output_path(title, url, now=t1)
        p2 = build_summary_output_path(title, url, now=t2)
        self.assertNotEqual(os.path.basename(p1), os.path.basename(p2))


if __name__ == "__main__":
    unittest.main()
