from abc import ABC, abstractmethod


class SummarizerInterface(ABC):
    """
    Interface for summarization services.
    Any class that provides summarization functionality should implement this interface.
    """

    @abstractmethod
    def summarize(self, title, text):
        """
        Summarize the given text.

        Args:
            title (str): The title of the content to summarize.
            text (str): The text content to summarize.

        Returns:
            str: The summarized text.
        """
        pass
