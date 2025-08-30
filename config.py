import os
import pytz
from dotenv import load_dotenv


class Config:
    """
    Centralized configuration management for the application.
    Handles loading environment variables, setting defaults, and providing
    configuration values to other components.
    """

    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # Set timezone
        self.timezone = pytz.timezone("Asia/Taipei")

        # API keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.google_gemini_api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        self.notion_api_key = os.getenv("NOTION_API_KEY")
        self.notion_database_id = os.getenv("NOTION_DATABASE_ID")

        # File paths
        self.data_dir = "data"
        self.videos_dir = os.path.join(self.data_dir, "videos")
        self.summarized_dir = os.path.join(self.data_dir, "_summarized")

        # Ensure directories exist
        self._ensure_directories_exist()

        # Transcription settings
        self.transcription_model_size = "tiny"

        # File patterns to process
        self.file_patterns = [
            os.path.join(self.videos_dir, "*.mp3"),
            os.path.join(self.videos_dir, "*.mp4"),
            os.path.join(self.videos_dir, "*.m4a"),
            os.path.join(self.videos_dir, "*.webm"),
        ]

    def _ensure_directories_exist(self):
        """Ensure that required directories exist."""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.videos_dir, exist_ok=True)
        os.makedirs(self.summarized_dir, exist_ok=True)

    def validate(self):
        """
        Validate that required configuration values are set.
        Raises ValueError if validation fails.
        """
        # Check that at least one API key is set for summarization
        if not self.openai_api_key and not self.google_gemini_api_key:
            raise ValueError(
                "At least one of OPENAI_API_KEY or GOOGLE_GEMINI_API_KEY must be set"
            )

        # Check Notion API key and database ID if using Notion storage
        if self.notion_api_key and not self.notion_database_id:
            raise ValueError(
                "NOTION_DATABASE_ID must be set when NOTION_API_KEY is provided"
            )
