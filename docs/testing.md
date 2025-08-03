# Testing Documentation for YouTube Transcript Summarizer

This document provides an overview of the testing strategy and coverage for the YouTube Transcript Summarizer project.

## Testing Strategy

The project follows a comprehensive testing approach that includes:

1. **Unit Testing**: Testing individual components in isolation
2. **Integration Testing**: Testing the interaction between components
3. **Mocking**: Using mock objects to isolate components from their dependencies

### Unit Testing

Unit tests focus on testing individual components in isolation. Each component is tested independently of others by using mock objects for dependencies. This approach ensures that tests are fast, reliable, and focused on specific functionality.

### Integration Testing

Integration tests focus on testing the interaction between components. These tests verify that components work together correctly and that the application functions as a whole.

### Mocking

Mocking is used extensively to isolate components from their dependencies. This approach allows us to:

- Test components without relying on external services (e.g., OpenAI, Google Gemini, Notion)
- Control the behavior of dependencies to test different scenarios
- Make tests faster and more reliable

## Test Coverage

The project has comprehensive test coverage for all major components:

### FileManager

- `test_file_manager_updated.py`: Tests for the FileManager class
  - Sanitizing filenames
  - Saving text to files (both relative and absolute paths)
  - Deleting files
  - Deleting Zone.Identifier files
  - Getting files to process

### Transcriber

- `test_transcriber.py`: Tests for the Transcriber class
  - Initializing with and without a config object
  - Transcribing with faster-whisper
  - Transcribing with the original whisper
  - The main transcribe method

### Summarizer

- `test_summarizer.py`: Tests for the Summarizer class
  - Initializing with and without a config object
  - Getting the prompt template
  - Summarizing with OpenAI
  - Summarizing with Google Gemini
  - Summarizing with Ollama (both success and error cases)
  - The main summarize method

### YouTubeDownloader

- `test_youtube_downloader.py`: Tests for the YouTubeDownloader class
  - Downloading a video with yt-dlp
  - Handling errors when yt-dlp doesn't download any files
  - Downloading a video with pytube
  - The main download method

### SummaryStorage

- `test_summary_storage.py`: Tests for the SummaryStorage class
  - Splitting text into chunks
  - Initializing with and without a config object
  - Saving a summary when the Notion client is not available
  - Saving a summary when the Notion client is available
  - Saving a summary to Notion (both success and error cases)

### Config

- `test_config.py`: Tests for the Config class
  - Initializing the config
  - Initializing the config with environment variables
  - Ensuring directories exist
  - Validating the config (success case)
  - Validating the config when API keys are missing
  - Validating the config when the Notion database ID is missing

### Processor

- `test_processor.py`: Tests for the Processor class
  - Extracting titles from file paths
  - Successfully processing a file (happy path)
  - Handling errors during transcription
  - Handling errors during summarization

### Main

- `test_main.py`: Tests for the Main class
  - Initializing with dependencies
  - Initializing without dependencies (which creates the dependencies)
  - Running with files to process
  - Running with no files to process
  - The main entry point
  - The main entry point when an exception is raised

## Running Tests

To run all tests:

```bash
python -m unittest discover
```

To run a specific test file:

```bash
python -m unittest test_file_name.py
```

For example:

```bash
python -m unittest test_processor.py
```

## Adding New Tests

When adding new functionality to the project, it's important to add corresponding tests. Follow these guidelines:

1. Create a new test file with the naming convention `test_*.py`
2. Import the `unittest` module and the component you want to test
3. Create a test class that inherits from `unittest.TestCase`
4. Add test methods that start with `test_`
5. Use assertions to verify expected behavior
6. Use mocking to isolate the component from its dependencies

Example:

```python
import unittest
from unittest.mock import Mock, patch
from my_component import MyComponent

class TestMyComponent(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mock dependencies
        self.mock_dependency = Mock()
        
        # Create the component with mock dependencies
        self.component = MyComponent(dependency=self.mock_dependency)
    
    def test_my_method(self):
        """Test that my_method works correctly."""
        # Configure the mock
        self.mock_dependency.some_method.return_value = "expected_result"
        
        # Call the method under test
        result = self.component.my_method()
        
        # Verify the result
        self.assertEqual(result, "expected_result")
        
        # Verify that the dependency was called correctly
        self.mock_dependency.some_method.assert_called_once()
```

## Best Practices

1. **Isolation**: Test components in isolation using mocking
2. **Coverage**: Aim for high test coverage, especially for critical functionality
3. **Readability**: Write clear, readable tests with descriptive names
4. **Setup and Teardown**: Use setUp and tearDown methods to set up and clean up test fixtures
5. **Edge Cases**: Test edge cases and error conditions
6. **Assertions**: Use specific assertions (e.g., assertEqual, assertTrue) rather than generic ones
7. **Documentation**: Document tests with docstrings and comments