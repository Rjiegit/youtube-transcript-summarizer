import unittest
from unittest.mock import Mock, patch
import os
from youtube_downloader import YouTubeDownloader


class TestYouTubeDownloader(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Set up common test data
        self.test_url = "https://www.youtube.com/watch?v=test_video_id"
        self.test_output_path = "data/test"
        self.test_video_path = os.path.join(
            self.test_output_path, "videos", "test_video.mp4"
        )
        self.test_video_title = "test_video"

        # Create a downloader
        self.downloader = YouTubeDownloader(self.test_url, self.test_output_path)

        # Ensure test directories exist
        os.makedirs(os.path.join(self.test_output_path, "videos"), exist_ok=True)

    @patch("youtube_downloader.subprocess.run")
    @patch("youtube_downloader.os.path.getctime")
    @patch("youtube_downloader.os.listdir")
    def test_download_with_yt_dlp(self, mock_listdir, mock_getctime, mock_run):
        """Test downloading a video with yt-dlp."""
        # Configure the mocks
        mock_listdir.return_value = ["test_video.mp4"]
        mock_getctime.return_value = 123456789

        # Call the method under test
        result = self.downloader._download_with_yt_dlp()

        # Verify the result
        expected_result = {
            "path": os.path.join(self.test_output_path, "videos", "test_video.mp4"),
            "title": "test_video",
        }
        self.assertEqual(result, expected_result)

        # Verify that subprocess.run was called with the correct parameters
        mock_run.assert_called_once_with(
            [
                "yt-dlp",
                "-S",
                "res:360",
                "-o",
                os.path.join(self.test_output_path, "videos", "%(title)s.%(ext)s"),
                self.test_url,
            ],
            check=True,
        )

    @patch("youtube_downloader.os.listdir")
    def test_download_with_yt_dlp_no_files(self, mock_listdir):
        """Test downloading a video with yt-dlp when no files are downloaded."""
        # Configure the mock to return an empty list
        mock_listdir.return_value = []

        # Call the method under test and verify that it raises an exception
        with self.assertRaises(Exception) as context:
            self.downloader._download_with_yt_dlp()

        # Verify the exception message
        self.assertEqual(
            str(context.exception), "yt-dlp did not download any video file."
        )

    @patch("youtube_downloader.YouTube")
    def test_download_with_pytube(self, mock_youtube_class):
        """Test downloading a video with pytube."""
        # Configure the mocks
        mock_youtube = Mock()
        mock_youtube_class.return_value = mock_youtube
        mock_youtube.title = self.test_video_title

        mock_stream = Mock()
        mock_stream.download.return_value = self.test_video_path
        mock_youtube.streams.filter.return_value.first.return_value = mock_stream

        # Call the method under test
        result = self.downloader._download_with_pytube()

        # Verify the result
        expected_result = {"path": self.test_video_path, "title": self.test_video_title}
        self.assertEqual(result, expected_result)

        # Verify that YouTube was called with the correct parameters
        mock_youtube_class.assert_called_once_with(
            self.test_url, on_progress_callback=unittest.mock.ANY
        )

        # Verify that the streams were filtered correctly
        mock_youtube.streams.filter.assert_called_once_with(only_audio=True)

        # Verify that download was called with the correct parameters
        mock_stream.download.assert_called_once_with(output_path=self.test_output_path)

    @patch("youtube_downloader.YouTubeDownloader._download_with_yt_dlp")
    def test_download(self, mock_download_with_yt_dlp):
        """Test the download method, which should call _download_with_yt_dlp."""
        # Configure the mock
        expected_result = {"path": self.test_video_path, "title": self.test_video_title}
        mock_download_with_yt_dlp.return_value = expected_result

        # Call the method under test
        result = self.downloader.download()

        # Verify the result
        self.assertEqual(result, expected_result)

        # Verify that _download_with_yt_dlp was called
        mock_download_with_yt_dlp.assert_called_once()


if __name__ == "__main__":
    unittest.main()
