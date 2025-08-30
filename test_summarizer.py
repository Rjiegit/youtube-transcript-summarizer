import unittest
from unittest.mock import Mock, patch, MagicMock
from summarizer import Summarizer


class TestSummarizer(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a mock config
        self.mock_config = Mock()
        self.mock_config.openai_api_key = "test_openai_key"
        self.mock_config.google_gemini_api_key = "test_gemini_key"

        # Create a summarizer with the mock config
        self.summarizer = Summarizer(config=self.mock_config)

        # Set up common test data
        self.test_title = "Test Title"
        self.test_text = "This is a test text to summarize."
        self.test_summary = "This is a test summary."
        self.test_prompt = "This is a test prompt."

    @patch("summarizer.prompt.PROMPT_2")
    def test_get_prompt(self, mock_prompt):
        """Test getting the prompt template."""
        # Configure the mock
        mock_prompt.format.return_value = self.test_prompt

        # Call the method under test
        result = self.summarizer.get_prompt(self.test_title, self.test_text)

        # Verify the result
        self.assertEqual(result, self.test_prompt)

        # Verify that the format method was called with the correct parameters
        mock_prompt.format.assert_called_once_with(
            title=self.test_title, text=self.test_text
        )

    @patch("summarizer.openai")
    @patch("summarizer.Summarizer.get_prompt")
    def test_summarize_with_openai(self, mock_get_prompt, mock_openai):
        """Test summarizing with OpenAI."""
        # Configure the mocks
        mock_get_prompt.return_value = self.test_prompt
        mock_completion = Mock()
        mock_completion.choices[0].text = self.test_summary
        mock_openai.Completion.create.return_value = mock_completion

        # Call the method under test
        result = self.summarizer.summarize_with_openai(self.test_title, self.test_text)

        # Verify the result
        self.assertEqual(result, self.test_summary)

        # Verify that the API key was set
        self.assertEqual(mock_openai.api_key, self.mock_config.openai_api_key)

        # Verify that the create method was called with the correct parameters
        mock_openai.Completion.create.assert_called_once_with(
            engine="gpt-4o-mini", prompt=self.test_prompt, temperature=0.5
        )

    @patch("summarizer.genai")
    @patch("summarizer.Summarizer.get_prompt")
    def test_summarize_with_google_gemini(self, mock_get_prompt, mock_genai):
        """Test summarizing with Google Gemini."""
        # Configure the mocks
        mock_get_prompt.return_value = self.test_prompt
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = self.test_summary
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        # Call the method under test
        result = self.summarizer.summarize_with_google_gemini(
            self.test_title, self.test_text
        )

        # Verify the result
        self.assertEqual(result, self.test_summary)

        # Verify that the API key was configured
        mock_genai.configure.assert_called_once_with(
            api_key=self.mock_config.google_gemini_api_key
        )

        # Verify that the GenerativeModel was created with the correct parameters
        mock_genai.GenerativeModel.assert_called_once_with("gemini-2.0-flash")

        # Verify that the generate_content method was called with the correct parameters
        mock_model.generate_content.assert_called_once_with(self.test_prompt)

    @patch("summarizer.requests.post")
    @patch("summarizer.Summarizer.get_prompt")
    def test_summarize_with_ollama(self, mock_get_prompt, mock_post):
        """Test summarizing with Ollama."""
        # Configure the mocks
        mock_get_prompt.return_value = self.test_prompt
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": self.test_summary}
        mock_post.return_value = mock_response

        # Call the method under test
        result = self.summarizer.summarize_with_ollama(self.test_title, self.test_text)

        # Verify the result
        self.assertEqual(result, self.test_summary)

        # Verify that the post method was called with the correct parameters
        mock_post.assert_called_once_with(
            "http://host.docker.internal:11434/api/generate",
            headers={"Content-Type": "application/json"},
            json={"model": "llama3.2", "prompt": self.test_prompt, "stream": False},
        )

    @patch("summarizer.requests.post")
    @patch("summarizer.Summarizer.get_prompt")
    def test_summarize_with_ollama_error(self, mock_get_prompt, mock_post):
        """Test summarizing with Ollama when there's an error."""
        # Configure the mocks
        mock_get_prompt.return_value = self.test_prompt
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        # Call the method under test and verify that it raises an exception
        with self.assertRaises(Exception) as context:
            self.summarizer.summarize_with_ollama(self.test_title, self.test_text)

        # Verify the exception message
        self.assertIn(
            "Error from Ollama API: 500 Internal Server Error", str(context.exception)
        )

    @patch("summarizer.Summarizer.summarize_with_google_gemini")
    def test_summarize(self, mock_summarize_with_google_gemini):
        """Test the summarize method, which should call summarize_with_google_gemini."""
        # Configure the mock
        mock_summarize_with_google_gemini.return_value = self.test_summary

        # Call the method under test
        result = self.summarizer.summarize(self.test_title, self.test_text)

        # Verify the result
        self.assertEqual(result, self.test_summary)

        # Verify that summarize_with_google_gemini was called with the correct parameters
        mock_summarize_with_google_gemini.assert_called_once_with(
            self.test_title, self.test_text
        )

    def test_init_with_config(self):
        """Test initializing the summarizer with a config object."""
        # Create a summarizer with the mock config
        summarizer = Summarizer(config=self.mock_config)

        # Verify that the API keys were set from the config
        self.assertEqual(summarizer.openai_api_key, self.mock_config.openai_api_key)
        self.assertEqual(
            summarizer.google_gemini_api_key, self.mock_config.google_gemini_api_key
        )

    @patch("summarizer.load_dotenv")
    @patch("summarizer.os.getenv")
    def test_init_without_config(self, mock_getenv, mock_load_dotenv):
        """Test initializing the summarizer without a config object."""
        # Configure the mock
        mock_getenv.side_effect = lambda key: {
            "OPENAI_API_KEY": "env_openai_key",
            "GOOGLE_GEMINI_API_KEY": "env_gemini_key",
        }.get(key)

        # Create a summarizer without a config
        summarizer = Summarizer()

        # Verify that load_dotenv was called
        mock_load_dotenv.assert_called_once()

        # Verify that the API keys were set from the environment variables
        self.assertEqual(summarizer.openai_api_key, "env_openai_key")
        self.assertEqual(summarizer.google_gemini_api_key, "env_gemini_key")


if __name__ == "__main__":
    unittest.main()
