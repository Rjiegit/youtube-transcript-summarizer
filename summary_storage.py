import os
from notion_client import Client
from dotenv import load_dotenv
from logger import logger
from interfaces.summary_storage_interface import SummaryStorageInterface


class SummaryStorage(SummaryStorageInterface):
    """
    SummaryStorage class that implements the SummaryStorageInterface.
    Provides methods to store summaries in various backends, currently supporting Notion.
    """

    def __init__(self, config=None):
        """
        Initialize the summary storage with configuration.

        Args:
            config (Config, optional): Configuration object. If provided, uses API keys from config.
        """
        # Load environment variables if config is not provided
        if not config:
            load_dotenv()
            self.notion_api_key = os.getenv("NOTION_API_KEY")
            self.notion_database_id = os.getenv("NOTION_DATABASE_ID")
        else:
            self.notion_api_key = config.notion_api_key
            self.notion_database_id = config.notion_database_id

        # Initialize Notion client if API key is available
        if self.notion_api_key:
            self.notion_client = Client(auth=self.notion_api_key)
        else:
            self.notion_client = None

    def save(self, title, text, model, url):
        """
        Save a summary to storage.

        Args:
            title (str): The title of the summary.
            text (str): The summarized text content.
            model (str): The model used for summarization.
            url (str): The source URL or file path.
        """
        if self.notion_client and self.notion_database_id:
            self.save_with_notion(title, text, model, url)
        else:
            logger.warning("Notion API key or database ID not set. Summary not saved to Notion.")

    def split_text(self, text, limit=2000):
        """
        Split text into chunks of specified size for Notion API.

        Args:
            text (str): The text to split.
            limit (int, optional): Maximum chunk size. Defaults to 2000.

        Returns:
            list: List of text chunks.
        """
        return [text[i:i + limit] for i in range(0, len(text), limit)]

    def save_with_notion(self, title, text, model, url):
        """
        Save a summary to Notion.

        Args:
            title (str): The title of the summary.
            text (str): The summarized text content.
            model (str): The model used for summarization.
            url (str): The source URL or file path.
        """
        if not self.notion_client or not self.notion_database_id:
            raise ValueError("Notion API key or database ID not set.")

        try:
            text_chunks = self.split_text(text, limit=2000)

            children = [
                {
                    "object": 'block',
                    "paragraph": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": chunk,
                                },
                            },
                        ],
                        "color": 'default',
                    }
                } for chunk in text_chunks
            ]

            response = self.notion_client.pages.create(
                parent={"database_id": self.notion_database_id},
                properties={
                    "Title": {
                        "title": [
                            {
                                "text": {
                                    "content": title,
                                },
                            },
                        ],
                    },
                    "URL": {
                        "url": url,
                    },
                    "Model": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": model,
                                },
                            },
                        ],
                    },
                    "Public": {
                        "checkbox": False,
                    },
                },
                children=children
            )
            logger.info(f"Summary successfully added to Notion! Page ID: {response['id']}")
        except Exception as e:
            logger.error(f"Error saving to Notion: {e}")
