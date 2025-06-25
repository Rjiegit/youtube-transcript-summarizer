import whisper
import os
from faster_whisper import WhisperModel
from logger import logger
from interfaces.transcriber_interface import TranscriberInterface

class Transcriber(TranscriberInterface):
    def __init__(self, config=None, model_size="base"):
        """
        Initialize the transcriber with configuration.

        Args:
            config (Config, optional): Configuration object. If provided, uses model_size from config.
            model_size (str, optional): Size of the Whisper model to use. Defaults to "base".
        """
        self.model_size = config.transcription_model_size if config else model_size

    def transcribe(self, file_path):
        """
        Transcribe audio/video file to text.

        Args:
            file_path (str): Path to the audio/video file to transcribe.

        Returns:
            str: The transcribed text.
        """
        return self.transcribe_with_faster_whisper(file_path)

    def transcribe_with_whisper(self, file_path):
        """
        Transcribe using the original Whisper model.

        Args:
            file_path (str): Path to the audio/video file to transcribe.

        Returns:
            str: The transcribed text.
        """
        logger.info(f"Transcribing audio with Whisper...")
        whisper_model = whisper.load_model(self.model_size)
        result = whisper_model.transcribe(file_path, verbose=True, fp16=False)
        return result['text']

    def transcribe_with_faster_whisper(self, file_path):
        """
        Transcribe using the faster-whisper implementation.

        Args:
            file_path (str): Path to the audio/video file to transcribe.

        Returns:
            str: The transcribed text.
        """
        logger.info(f"Transcribing audio with Faster Whisper...")
        whisper_model = WhisperModel(
            self.model_size, 
            compute_type="int8",
            )
        segments, _ = whisper_model.transcribe(file_path)

        transcript_text = ""
        for segment in segments:
            # print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
            transcript_text += segment.text
        return transcript_text
