from abc import ABC, abstractmethod


class FileManagerInterface(ABC):
    """
    Interface for file management services.
    Any class that provides file management functionality should implement this interface.
    """

    @abstractmethod
    def sanitize_filename(self, filename):
        """
        Sanitize a filename by removing invalid characters.

        Args:
            filename (str): The filename to sanitize.

        Returns:
            str: The sanitized filename.
        """
        pass

    @abstractmethod
    def save_text(self, text, output_file):
        """
        Save text content to a file.

        Args:
            text (str): The text content to save.
            output_file (str): The path where the file should be saved.
        """
        pass

    @abstractmethod
    def delete_file(self, file_path):
        """
        Delete a file from the filesystem.

        Args:
            file_path (str): The path of the file to delete.
        """
        pass
