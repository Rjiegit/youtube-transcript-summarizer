# Development Guidelines for YouTube Transcript Summarizer

This document provides essential information for developers working on this project. It includes build/configuration instructions, testing information, and additional development details.

## Build/Configuration Instructions

### Environment Setup

#### Docker Setup (Recommended)
1. **Start Docker Services**:
   ```bash
   docker compose up -d
   ```

2. **Enter the Container**:
   ```bash
   docker compose exec app bash
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

#### Local Setup (Alternative)
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install yt-dlp** (for YouTube video downloading):
   ```bash
   make install
   ```

### Configuration

1. **API Keys**:
   Create a `.env` file in the project root with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key
   GOOGLE_GEMINI_API_KEY=your_gemini_api_key
   NOTION_API_KEY=your_notion_api_key
   NOTION_DATABASE_ID=your_notion_database_id
   ```

   Note: At least one of OpenAI or Google Gemini API keys is required for summarization.

2. **Ollama Setup** (Optional):
   If you want to use Ollama for local LLM processing:
   ```bash
   ollama serve
   ollama pull llama3.2
   ```

### Model Configuration

- **Transcription Model**: The default model size for Whisper is "tiny". You can change this in `main.py` by modifying the `model_size` parameter when initializing the `Transcriber`.

- **Summarization Model**: By default, the project uses Google Gemini. You can switch to OpenAI or Ollama by modifying the `summarize` method in `summarizer.py` to call the appropriate method.

## Testing Information

### Running Tests

The project uses Python's built-in `unittest` framework for testing. To run tests:

```bash
python3 -m unittest discover
```

To run a specific test file:

```bash
python3 -m unittest test_file_name.py
```

### Adding New Tests

1. Create a new test file with the naming convention `test_*.py`
2. Import the `unittest` module and the component you want to test
3. Create a test class that inherits from `unittest.TestCase`
4. Add test methods that start with `test_`
5. Use assertions to verify expected behavior

Example:

```python
import unittest
from file_manager import FileManager

class TestFileManager(unittest.TestCase):
    def test_sanitize_filename(self):
        dirty_filename = 'test/file:with*invalid?chars<>|'
        clean_filename = FileManager.sanitize_filename(dirty_filename)
        expected = 'test_file_with_invalid_chars___'
        self.assertEqual(clean_filename, expected)
```

### Test Data

- Create test data in the `data/test` directory
- Clean up test data after tests complete
- Use temporary files/directories when possible

## Additional Development Information

### Project Structure

- **main.py**: Entry point that orchestrates the workflow
- **transcriber.py**: Handles audio/video transcription using Whisper
- **summarizer.py**: Generates summaries using various LLM providers
- **file_manager.py**: Manages file operations
- **summary_storage.py**: Stores summaries in Notion
- **prompt.py**: Contains prompt templates for LLMs
- **youtube_downloader.py**: Utility for downloading YouTube videos

### Workflow

1. Videos are downloaded to `data/videos/` using yt-dlp
2. The main process transcribes each video using Whisper
3. The transcription is summarized using an LLM
4. Summaries are saved to `data/_summarized/` and optionally to Notion
5. Original video files are deleted after processing

### Error Handling

- The application uses try/except blocks to handle errors during processing
- Failed files are deleted to prevent repeated processing attempts
- Errors are logged to the console

### Internationalization

- The project is primarily designed for Chinese content
- Prompts are configured for Chinese output with English technical terms
- Output is formatted in Markdown

### Performance Considerations

- The application processes files sequentially
- Transcription is the most resource-intensive operation
- Using faster-whisper improves performance over standard whisper
- Model size affects both accuracy and performance (tiny, base, small, medium, large)

### Extending the Project

To add support for a new LLM provider:
1. Add the required dependencies to `requirements.txt`
2. Create a new method in the `Summarizer` class (e.g., `summarize_with_new_provider`)
3. Update the `summarize` method to call your new method
4. Add any required API keys to the `.env` file and load them in the constructor