from abc import ABC, abstractmethod


class SummarizerInterface(ABC):
    """
    Interface for summarization services.
    Any class that provides summarization functionality should implement this interface.
    """

    @abstractmethod
    def summarize(self, title, text, metadata=None):
        """
        Summarize the given text.

        Args:
            title (str): The title of the content to summarize.
            text (str): The text content to summarize.
            metadata: Optional curated source metadata for context.

        Returns:
            str: The summarized text.
        """
        pass
