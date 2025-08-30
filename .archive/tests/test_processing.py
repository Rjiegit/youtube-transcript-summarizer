
import pytest
from unittest.mock import MagicMock, patch
from processing import _process_task
from database.task import Task

@patch('processing.YouTubeDownloader')
@patch('processing.Transcriber')
@patch('processing.Summarizer')
@patch('processing.FileManager')
@patch('processing.SummaryStorage')
def test_process_task_success(
    MockSummaryStorage, MockFileManager, MockSummarizer, MockTranscriber, MockDownloader
):
    """
    Tests the successful processing of a single task.
    """
    # Arrange
    mock_db = MagicMock()
    mock_downloader_instance = MockDownloader.return_value
    mock_downloader_instance.download.return_value = {
        "path": "data/test_video.mp4",
        "title": "Test Video Title"
    }
    mock_transcriber_instance = MockTranscriber.return_value
    mock_transcriber_instance.transcribe.return_value = "This is a transcription."
    mock_summarizer_instance = MockSummarizer.return_value
    mock_summarizer_instance.summarize.return_value = "This is a summary."
    mock_storage_instance = MockSummaryStorage.return_value

    task = Task(id=1, url="http://fakeurl.com/video", status="Pending", title="Initial Title")

    # Act
    _process_task(task, mock_db)

    # Assert
    # 1. Status updated to Processing
    mock_db.update_task_status.assert_any_call(1, "Processing", title="Initial Title")

    # 2. Downloader called
    MockDownloader.assert_called_with("http://fakeurl.com/video", output_path="data")
    mock_downloader_instance.download.assert_called_once()

    # 3. Transcriber called
    MockTranscriber.assert_called_once()
    mock_transcriber_instance.transcribe.assert_called_with("data/test_video.mp4")

    # 4. Summarizer called
    MockSummarizer.assert_called_once()
    mock_summarizer_instance.summarize.assert_called_with("Test Video Title", "This is a transcription.")

    # 5. Summary saved to file
    MockFileManager.sanitize_filename.assert_called_with("Test Video Title")
    sanitized_title = MockFileManager.sanitize_filename.return_value
    MockFileManager.save_text.assert_called_with("This is a summary.", f"data/summaries/{sanitized_title}.md")

    # 6. Summary saved to storage
    mock_storage_instance.save.assert_called_with(
        title="Test Video Title",
        text="This is a summary.",
        model="whisper-openai",
        url="http://fakeurl.com/video"
    )

    # 7. Status updated to Completed
    mock_db.update_task_status.assert_called_with(
        1,
        "Completed",
        title="Test Video Title",
        summary="This is a summary.",
        processing_duration=pytest.approx(0, abs=10)  # Allow for some processing time
    )
    assert mock_db.update_task_status.call_count == 2

@patch('processing.YouTubeDownloader')
def test_process_task_failure(MockDownloader):
    """
    Tests the handling of a failure during task processing.
    """
    # Arrange
    mock_db = MagicMock()
    mock_downloader_instance = MockDownloader.return_value
    error_message = "Download failed"
    mock_downloader_instance.download.side_effect = Exception(error_message)

    task = Task(id=2, url="http://fakeurl.com/video", status="Pending")

    # Act
    _process_task(task, mock_db)

    # Assert
    # 1. Status updated to Processing
    mock_db.update_task_status.assert_any_call(2, "Processing", title=None)

    # 2. Status updated to Failed
    mock_db.update_task_status.assert_called_with(
        2,
        "Failed",
        error_message=error_message,
        processing_duration=pytest.approx(0, abs=2)
    )
    assert mock_db.update_task_status.call_count == 2
