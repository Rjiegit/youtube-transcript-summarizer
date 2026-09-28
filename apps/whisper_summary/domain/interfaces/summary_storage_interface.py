from abc import ABC, abstractmethod


class SummaryStorageInterface(ABC):
    """
    Interface for summary storage services.
    Any class that provides summary storage functionality should implement this interface.
    """

    @abstractmethod
    def save(self, title, text, model, url):
        """
        Save a summary to storage.

        Args:
            title (str): The title of the summary.
            text (str): The summarized text content.
            model (str): The model used for summarization.
            url (str): The source URL or file path.
        """
        pass
