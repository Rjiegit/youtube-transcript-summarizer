import json
import os
import tempfile
import types
import unittest
from unittest.mock import patch

from src.infrastructure.media.downloader import YouTubeDownloader


class TestYouTubeDownloaderMetadata(unittest.TestCase):
    def test_download_returns_curated_metadata_from_json_print(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            video_dir = os.path.join(tmpdir, "videos")
            os.makedirs(video_dir)
            video_path = os.path.join(video_dir, "dQw4w9WgXcQ.mp4")
            with open(video_path, "wb") as video_file:
                video_file.write(b"video")

            raw_metadata = {
                "id": "dQw4w9WgXcQ",
                "title": "測試影片",
                "description": "第一行\n第二行",
                "channel": "測試頻道",
                "channel_id": "UC123",
                "upload_date": "20260830",
                "duration": 125.5,
                "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "chapters": [
                    {"title": "開始", "start_time": 0, "end_time": 60.5},
                    {"title": "結論", "start_time": 60.5, "end_time": 125.5},
                ],
            }
            stdout = "\n".join(
                [
                    f"__YT_DLP_METADATA__={json.dumps(raw_metadata, ensure_ascii=False)}",
                    f"__YT_DLP_PATH__={video_path}",
                ]
            )

            with patch(
                "src.infrastructure.media.downloader.subprocess.run",
                return_value=types.SimpleNamespace(stdout=stdout, stderr=""),
            ) as mock_run:
                result = YouTubeDownloader(
                    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    output_path=tmpdir,
                ).download()

            command = mock_run.call_args.args[0]
            self.assertTrue(
                any(
                    "description,channel,channel_id,upload_date" in argument
                    for argument in command
                )
            )

        metadata = result["metadata"]
        self.assertEqual(result["title"], "測試影片")
        self.assertEqual(metadata.video_id, "dQw4w9WgXcQ")
        self.assertEqual(metadata.description, "第一行\n第二行")
        self.assertEqual(metadata.upload_date, "2026-08-30")
        self.assertEqual(metadata.duration_seconds, 125.5)
        self.assertEqual(metadata.chapters[1].title, "結論")

    def test_invalid_metadata_json_does_not_fail_a_valid_download(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            video_dir = os.path.join(tmpdir, "videos")
            os.makedirs(video_dir)
            video_path = os.path.join(video_dir, "dQw4w9WgXcQ.mp4")
            with open(video_path, "wb") as video_file:
                video_file.write(b"video")

            stdout = "\n".join(
                [
                    "__YT_DLP_METADATA__={invalid-json}",
                    f"__YT_DLP_PATH__={video_path}",
                    "__YT_DLP_TITLE__=Fallback title",
                ]
            )
            with patch(
                "src.infrastructure.media.downloader.subprocess.run",
                return_value=types.SimpleNamespace(stdout=stdout, stderr=""),
            ):
                result = YouTubeDownloader(
                    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    output_path=tmpdir,
                ).download()

        self.assertEqual(result["title"], "Fallback title")
        self.assertIsNone(result["metadata"].description)


if __name__ == "__main__":
    unittest.main()
