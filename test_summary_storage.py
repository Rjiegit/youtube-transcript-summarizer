import unittest
from unittest.mock import Mock, patch
from summary_storage import SummaryStorage

class TestSummaryStorage(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock config
        self.mock_config = Mock()
        self.mock_config.notion_api_key = "test_notion_key"
        self.mock_config.notion_database_id = "test_database_id"
        
        # Create a summary storage with the mock config
        self.summary_storage = SummaryStorage(config=self.mock_config)
        
        # Set up common test data
        self.test_title = "Test Title"
        self.test_text = "This is a test summary text."
        self.test_model = "test_model"
        self.test_url = "https://example.com/test"
    
    def test_split_text(self):
        """Test splitting text into chunks."""
        # Test with a short text (less than the limit)
        short_text = "Short text"
        result = self.summary_storage.split_text(short_text, limit=20)
        self.assertEqual(result, [short_text])
        
        # Test with a long text (more than the limit)
        long_text = "This is a longer text that should be split into multiple chunks."
        limit = 20
        result = self.summary_storage.split_text(long_text, limit=limit)
        
        # Verify that each chunk is no longer than the limit
        for chunk in result:
            self.assertLessEqual(len(chunk), limit)
        
        # Verify that the concatenated chunks equal the original text
        self.assertEqual(''.join(result), long_text)
    
    @patch('summary_storage.Client')
    def test_init_with_config(self, mock_client_class):
        """Test initializing the summary storage with a config object."""
        # Configure the mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Create a summary storage with the mock config
        summary_storage = SummaryStorage(config=self.mock_config)
        
        # Verify that the API keys were set from the config
        self.assertEqual(summary_storage.notion_api_key, self.mock_config.notion_api_key)
        self.assertEqual(summary_storage.notion_database_id, self.mock_config.notion_database_id)
        
        # Verify that the Notion client was created with the correct API key
        mock_client_class.assert_called_once_with(auth=self.mock_config.notion_api_key)
        self.assertEqual(summary_storage.notion_client, mock_client)
    
    @patch('summary_storage.load_dotenv')
    @patch('summary_storage.os.getenv')
    @patch('summary_storage.Client')
    def test_init_without_config(self, mock_client_class, mock_getenv, mock_load_dotenv):
        """Test initializing the summary storage without a config object."""
        # Configure the mocks
        mock_getenv.side_effect = lambda key: {
            "NOTION_API_KEY": "env_notion_key",
            "NOTION_DATABASE_ID": "env_database_id"
        }.get(key)
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Create a summary storage without a config
        summary_storage = SummaryStorage()
        
        # Verify that load_dotenv was called
        mock_load_dotenv.assert_called_once()
        
        # Verify that the API keys were set from the environment variables
        self.assertEqual(summary_storage.notion_api_key, "env_notion_key")
        self.assertEqual(summary_storage.notion_database_id, "env_database_id")
        
        # Verify that the Notion client was created with the correct API key
        mock_client_class.assert_called_once_with(auth="env_notion_key")
        self.assertEqual(summary_storage.notion_client, mock_client)
    
    def test_save_without_notion_client(self):
        """Test saving a summary when the Notion client is not available."""
        # Create a summary storage with no Notion client
        summary_storage = SummaryStorage()
        summary_storage.notion_client = None
        
        # Call the method under test (should not raise an exception)
        summary_storage.save(self.test_title, self.test_text, self.test_model, self.test_url)
    
    @patch('summary_storage.SummaryStorage.save_with_notion')
    def test_save_with_notion_client(self, mock_save_with_notion):
        """Test saving a summary when the Notion client is available."""
        # Call the method under test
        self.summary_storage.save(self.test_title, self.test_text, self.test_model, self.test_url)
        
        # Verify that save_with_notion was called with the correct parameters
        mock_save_with_notion.assert_called_once_with(self.test_title, self.test_text, self.test_model, self.test_url)
    
    @patch('summary_storage.SummaryStorage.split_text')
    def test_save_with_notion(self, mock_split_text):
        """Test saving a summary to Notion."""
        # Configure the mock
        text_chunks = ["Chunk 1", "Chunk 2"]
        mock_split_text.return_value = text_chunks
        
        # Create a spy on the Notion client's pages.create method
        with patch.object(self.summary_storage.notion_client.pages, 'create') as mock_create:
            # Configure the mock to return a response with an ID
            mock_create.return_value = {"id": "test_page_id"}
            
            # Call the method under test
            self.summary_storage.save_with_notion(self.test_title, self.test_text, self.test_model, self.test_url)
            
            # Verify that split_text was called with the correct parameters
            mock_split_text.assert_called_once_with(self.test_text, limit=2000)
            
            # Verify that pages.create was called with the correct parameters
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            
            # Check parent
            self.assertEqual(call_args["parent"], {"database_id": self.mock_config.notion_database_id})
            
            # Check properties
            properties = call_args["properties"]
            self.assertEqual(properties["Title"]["title"][0]["text"]["content"], self.test_title)
            self.assertEqual(properties["URL"]["url"], self.test_url)
            self.assertEqual(properties["Model"]["rich_text"][0]["text"]["content"], self.test_model)
            self.assertEqual(properties["Public"]["checkbox"], False)
            
            # Check children (blocks)
            children = call_args["children"]
            self.assertEqual(len(children), len(text_chunks))
            for i, chunk in enumerate(text_chunks):
                self.assertEqual(children[i]["paragraph"]["rich_text"][0]["text"]["content"], chunk)
    
    @patch('summary_storage.SummaryStorage.split_text')
    def test_save_with_notion_error(self, mock_split_text):
        """Test saving a summary to Notion when there's an error."""
        # Configure the mock
        text_chunks = ["Chunk 1", "Chunk 2"]
        mock_split_text.return_value = text_chunks
        
        # Create a spy on the Notion client's pages.create method
        with patch.object(self.summary_storage.notion_client.pages, 'create') as mock_create:
            # Configure the mock to raise an exception
            mock_create.side_effect = Exception("Notion API error")
            
            # Call the method under test (should not raise an exception)
            self.summary_storage.save_with_notion(self.test_title, self.test_text, self.test_model, self.test_url)
            
            # Verify that split_text was called with the correct parameters
            mock_split_text.assert_called_once_with(self.test_text, limit=2000)
            
            # Verify that pages.create was called
            mock_create.assert_called_once()

if __name__ == '__main__':
    unittest.main()