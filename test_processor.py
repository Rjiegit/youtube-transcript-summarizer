import unittest
from unittest.mock import Mock, patch
from processor import Processor
import os
from datetime import datetime

class TestProcessor(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mock objects for dependencies
        self.mock_transcriber = Mock()
        self.mock_summarizer = Mock()
        self.mock_file_manager = Mock()
        self.mock_summary_storage = Mock()
        self.mock_config = Mock()
        
        # Create processor with mock dependencies
        self.processor = Processor(
            transcriber=self.mock_transcriber,
            summarizer=self.mock_summarizer,
            file_manager=self.mock_file_manager,
            summary_storage=self.mock_summary_storage,
            config=self.mock_config
        )
        
        # Set up common test data
        self.test_file_path = "data/videos/test_video.mp4"
        self.test_title = "test_video"
        self.test_transcription = "This is a test transcription."
        self.test_summary = "This is a test summary."
    
    def test_extract_title(self):
        """Test that _extract_title correctly extracts the title from a file path."""
        # Test with a simple file path
        result = self.processor._extract_title(self.test_file_path)
        self.assertEqual(result, self.test_title)
        
        # Test with a more complex file path
        complex_path = "/path/to/some/directory/with a space/file-name_123.mp4"
        expected = "file-name_123"
        result = self.processor._extract_title(complex_path)
        self.assertEqual(result, expected)
    
    def test_process_file_success(self):
        """Test that process_file correctly processes a file when everything works."""
        # Configure mocks
        self.mock_transcriber.transcribe.return_value = self.test_transcription
        self.mock_summarizer.summarize.return_value = self.test_summary
        
        # Call the method under test
        result = self.processor.process_file(self.test_file_path)
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify that the dependencies were called correctly
        self.mock_transcriber.transcribe.assert_called_once_with(self.test_file_path)
        self.mock_summarizer.summarize.assert_called_once_with(self.test_title, self.test_transcription)
        self.mock_file_manager.save_text.assert_called_once()
        self.mock_summary_storage.save.assert_called_once()
        self.mock_file_manager.delete_file.assert_called_once_with(self.test_file_path)
    
    def test_process_file_transcription_error(self):
        """Test that process_file handles errors during transcription."""
        # Configure mock to raise an exception
        self.mock_transcriber.transcribe.side_effect = Exception("Transcription error")
        
        # Call the method under test
        result = self.processor.process_file(self.test_file_path)
        
        # Verify the result
        self.assertFalse(result)
        
        # Verify that the file was deleted
        self.mock_file_manager.delete_file.assert_called_once_with(self.test_file_path)
        
        # Verify that other methods were not called
        self.mock_summarizer.summarize.assert_not_called()
        self.mock_file_manager.save_text.assert_not_called()
        self.mock_summary_storage.save.assert_not_called()
    
    def test_process_file_summarization_error(self):
        """Test that process_file handles errors during summarization."""
        # Configure mocks
        self.mock_transcriber.transcribe.return_value = self.test_transcription
        self.mock_summarizer.summarize.side_effect = Exception("Summarization error")
        
        # Call the method under test
        result = self.processor.process_file(self.test_file_path)
        
        # Verify the result
        self.assertFalse(result)
        
        # Verify that the file was deleted
        self.mock_file_manager.delete_file.assert_called_once_with(self.test_file_path)
        
        # Verify that other methods were not called after the error
        self.mock_file_manager.save_text.assert_not_called()
        self.mock_summary_storage.save.assert_not_called()

if __name__ == '__main__':
    unittest.main()