import unittest
from unittest.mock import Mock, patch
from transcriber import Transcriber


class TestTranscriber(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock config
        self.mock_config = Mock()
        self.mock_config.transcription_model_size = "tiny"

        # Create a transcriber with the mock config
        self.transcriber = Transcriber(config=self.mock_config)

        # Set up common test data
        self.test_file_path = "data/videos/test_video.mp4"
        self.test_transcription = "This is a test transcription."

    @patch("transcriber.WhisperModel")
    def test_transcribe_with_faster_whisper(self, mock_whisper_model_class):
        """Test transcribing with faster-whisper."""
        # Configure the mock
        mock_whisper_model = Mock()
        mock_whisper_model_class.return_value = mock_whisper_model

        # Configure the segments
        mock_segment1 = Mock()
        mock_segment1.text = "This is "
        mock_segment2 = Mock()
        mock_segment2.text = "a test transcription."
        mock_segments = [mock_segment1, mock_segment2]

        # Configure the transcribe method to return the mock segments
        mock_whisper_model.transcribe.return_value = (mock_segments, None)

        # Call the method under test
        result = self.transcriber.transcribe_with_faster_whisper(self.test_file_path)

        # Verify the result
        self.assertEqual(result, self.test_transcription)

        # Verify that the WhisperModel was created with the correct parameters
        mock_whisper_model_class.assert_called_once_with(
            self.mock_config.transcription_model_size, compute_type="int8"
        )

        # Verify that the transcribe method was called with the correct parameters
        mock_whisper_model.transcribe.assert_called_once_with(self.test_file_path)

    @patch("transcriber.whisper")
    def test_transcribe_with_whisper(self, mock_whisper):
        """Test transcribing with the original whisper."""
        # Configure the mock
        mock_model = Mock()
        mock_whisper.load_model.return_value = mock_model

        # Configure the transcribe method to return a dictionary with the transcription
        mock_model.transcribe.return_value = {"text": self.test_transcription}

        # Call the method under test
        result = self.transcriber.transcribe_with_whisper(self.test_file_path)

        # Verify the result
        self.assertEqual(result, self.test_transcription)

        # Verify that the load_model method was called with the correct parameters
        mock_whisper.load_model.assert_called_once_with(
            self.mock_config.transcription_model_size
        )

        # Verify that the transcribe method was called with the correct parameters
        mock_model.transcribe.assert_called_once_with(
            self.test_file_path, verbose=True, fp16=False
        )

    @patch("transcriber.Transcriber.transcribe_with_faster_whisper")
    def test_transcribe(self, mock_transcribe_with_faster_whisper):
        """Test the transcribe method, which should call transcribe_with_faster_whisper."""
        # Configure the mock
        mock_transcribe_with_faster_whisper.return_value = self.test_transcription

        # Call the method under test
        result = self.transcriber.transcribe(self.test_file_path)

        # Verify the result
        self.assertEqual(result, self.test_transcription)

        # Verify that transcribe_with_faster_whisper was called with the correct parameters
        mock_transcribe_with_faster_whisper.assert_called_once_with(self.test_file_path)

    def test_init_with_config(self):
        """Test initializing the transcriber with a config object."""
        # Create a transcriber with the mock config
        transcriber = Transcriber(config=self.mock_config)

        # Verify that the model_size was set from the config
        self.assertEqual(
            transcriber.model_size, self.mock_config.transcription_model_size
        )

    def test_init_without_config(self):
        """Test initializing the transcriber without a config object."""
        # Create a transcriber without a config
        model_size = "base"
        transcriber = Transcriber(model_size=model_size)

        # Verify that the model_size was set from the parameter
        self.assertEqual(transcriber.model_size, model_size)


if __name__ == "__main__":
    unittest.main()
