from abc import ABC, abstractmethod


class TranscriberInterface(ABC):
    """
    Interface for transcription services.
    Any class that provides transcription functionality should implement this interface.
    """

    @abstractmethod
    def transcribe(self, file_path):
        """
        Transcribe audio/video file to text.

        Args:
            file_path (str): Path to the audio/video file to transcribe.

        Returns:
            str: The transcribed text.
        """
        pass
