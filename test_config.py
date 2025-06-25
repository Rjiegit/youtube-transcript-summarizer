import unittest
from unittest.mock import patch, Mock
import os
import pytz
from config import Config

class TestConfig(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for testing
        os.makedirs("data/test", exist_ok=True)
    
    def tearDown(self):
        """Clean up after each test method."""
        # Remove the temporary directory
        if os.path.exists("data/test"):
            import shutil
            shutil.rmtree("data/test")
    
    @patch('config.load_dotenv')
    def test_init(self, mock_load_dotenv):
        """Test initializing the config."""
        # Create a config
        config = Config()
        
        # Verify that load_dotenv was called
        mock_load_dotenv.assert_called_once()
        
        # Verify that the timezone was set correctly
        self.assertEqual(config.timezone, pytz.timezone("Asia/Taipei"))
        
        # Verify that the directories were created
        self.assertTrue(os.path.exists(config.data_dir))
        self.assertTrue(os.path.exists(config.videos_dir))
        self.assertTrue(os.path.exists(config.summarized_dir))
        
        # Verify that the transcription model size was set correctly
        self.assertEqual(config.transcription_model_size, "tiny")
        
        # Verify that the file patterns were set correctly
        self.assertEqual(len(config.file_patterns), 4)
        for pattern in config.file_patterns:
            self.assertTrue(pattern.startswith(config.videos_dir))
    
    @patch('config.os.getenv')
    @patch('config.load_dotenv')
    def test_init_with_env_vars(self, mock_load_dotenv, mock_getenv):
        """Test initializing the config with environment variables."""
        # Configure the mock
        mock_getenv.side_effect = lambda key: {
            "OPENAI_API_KEY": "test_openai_key",
            "GOOGLE_GEMINI_API_KEY": "test_gemini_key",
            "NOTION_API_KEY": "test_notion_key",
            "NOTION_DATABASE_ID": "test_database_id"
        }.get(key)
        
        # Create a config
        config = Config()
        
        # Verify that the API keys were set from the environment variables
        self.assertEqual(config.openai_api_key, "test_openai_key")
        self.assertEqual(config.google_gemini_api_key, "test_gemini_key")
        self.assertEqual(config.notion_api_key, "test_notion_key")
        self.assertEqual(config.notion_database_id, "test_database_id")
    
    def test_ensure_directories_exist(self):
        """Test that _ensure_directories_exist creates the required directories."""
        # Create a config with custom directories
        config = Config()
        config.data_dir = "data/test/custom_data"
        config.videos_dir = "data/test/custom_data/custom_videos"
        config.summarized_dir = "data/test/custom_data/custom_summarized"
        
        # Call the method under test
        config._ensure_directories_exist()
        
        # Verify that the directories were created
        self.assertTrue(os.path.exists(config.data_dir))
        self.assertTrue(os.path.exists(config.videos_dir))
        self.assertTrue(os.path.exists(config.summarized_dir))
    
    @patch('config.os.getenv')
    @patch('config.load_dotenv')
    def test_validate_success(self, mock_load_dotenv, mock_getenv):
        """Test validating the config when it's valid."""
        # Configure the mock
        mock_getenv.side_effect = lambda key: {
            "OPENAI_API_KEY": "test_openai_key",
            "NOTION_API_KEY": "test_notion_key",
            "NOTION_DATABASE_ID": "test_database_id"
        }.get(key)
        
        # Create a config
        config = Config()
        
        # Call the method under test (should not raise an exception)
        config.validate()
    
    @patch('config.os.getenv')
    @patch('config.load_dotenv')
    def test_validate_missing_api_keys(self, mock_load_dotenv, mock_getenv):
        """Test validating the config when both API keys are missing."""
        # Configure the mock to return None for API keys
        mock_getenv.return_value = None
        
        # Create a config
        config = Config()
        
        # Call the method under test and verify that it raises an exception
        with self.assertRaises(ValueError) as context:
            config.validate()
        
        # Verify the exception message
        self.assertEqual(str(context.exception), "At least one of OPENAI_API_KEY or GOOGLE_GEMINI_API_KEY must be set")
    
    @patch('config.os.getenv')
    @patch('config.load_dotenv')
    def test_validate_missing_notion_database_id(self, mock_load_dotenv, mock_getenv):
        """Test validating the config when the Notion API key is set but the database ID is missing."""
        # Configure the mock
        mock_getenv.side_effect = lambda key: {
            "OPENAI_API_KEY": "test_openai_key",
            "NOTION_API_KEY": "test_notion_key",
            "NOTION_DATABASE_ID": None
        }.get(key)
        
        # Create a config
        config = Config()
        
        # Call the method under test and verify that it raises an exception
        with self.assertRaises(ValueError) as context:
            config.validate()
        
        # Verify the exception message
        self.assertEqual(str(context.exception), "NOTION_DATABASE_ID must be set when NOTION_API_KEY is provided")

if __name__ == '__main__':
    unittest.main()