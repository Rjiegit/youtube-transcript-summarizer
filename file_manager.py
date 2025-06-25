import re
import os
import glob
from logger import logger
from interfaces.file_manager_interface import FileManagerInterface

class FileManager(FileManagerInterface):
    """
    FileManager class that implements the FileManagerInterface.
    Provides methods for file operations such as saving text, deleting files, and sanitizing filenames.
    """

    def __init__(self, config=None):
        """
        Initialize the file manager with configuration.

        Args:
            config (Config, optional): Configuration object. If provided, uses directory paths from config.
        """
        self.data_dir = config.data_dir if config else 'data'
        self.summarized_dir = config.summarized_dir if config else os.path.join(self.data_dir, '_summarized')

        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.summarized_dir, exist_ok=True)

    def sanitize_filename(self, filename):
        """
        Sanitize a filename by removing invalid characters.

        Args:
            filename (str): The filename to sanitize.

        Returns:
            str: The sanitized filename.
        """
        return re.sub(r'[\\/:*?"<>|]', '_', filename)

    def save_text(self, text, output_file):
        """
        Save text content to a file.

        Args:
            text (str): The text content to save.
            output_file (str): The path where the file should be saved.
        """
        logger.info(f"Saving text to {output_file}...")
        sanitized_file = self.sanitize_filename(output_file)

        # Determine if the path is relative or absolute
        if os.path.isabs(sanitized_file):
            full_path = sanitized_file
        else:
            full_path = os.path.join(self.data_dir, sanitized_file)

        # Ensure the directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as file:
            file.write(text)

        logger.info(f"Text saved to {full_path}")
        return full_path

    def delete_file(self, file_path):
        """
        Delete a file from the filesystem.

        Args:
            file_path (str): The path of the file to delete.
        """
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File {file_path} deleted.")
        else:
            logger.warning(f"File {file_path} not found.")

    def delete_zone_identifier_files(self, directory=None):
        """
        Delete Zone.Identifier files that are created when downloading files from the internet.

        Args:
            directory (str, optional): The directory to search for Zone.Identifier files.
                                      If not provided, uses the videos directory from config.
        """
        if directory is None:
            directory = os.path.join(self.data_dir, 'videos')

        zone_files = glob.glob(os.path.join(directory, "*Zone.Identifier"))
        try:
            for file_path in zone_files:
                self.delete_file(file_path)
        except Exception as e:
            logger.error(f"Error deleting Zone.Identifier files: {e}")

    def get_files_to_process(self, patterns=None):
        """
        Get a list of files to process based on the given patterns.

        Args:
            patterns (list, optional): List of glob patterns to match files.
                                      If not provided, uses default patterns.

        Returns:
            list: List of file paths to process.
        """
        if patterns is None:
            videos_dir = os.path.join(self.data_dir, 'videos')
            patterns = [
                os.path.join(videos_dir, "*.mp3"),
                os.path.join(videos_dir, "*.mp4"),
                os.path.join(videos_dir, "*.m4a"),
                os.path.join(videos_dir, "*.webm")
            ]

        files = []
        for pattern in patterns:
            files.extend(glob.glob(pattern))

        return files
