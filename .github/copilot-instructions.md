# GitHub Copilot Instructions

## Project Overview
This is a YouTube transcript summarizer built with Python that processes YouTube videos through a complete pipeline: download → transcribe → summarize → store. The system uses Whisper for transcription and multiple LLM providers (OpenAI, Google Gemini, Ollama) for summarization, all running in Docker containers.

## Architecture & Core Components

### Pipeline Flow
The main workflow follows this pattern:
1. **Download**: `youtube_downloader.py` uses yt-dlp to fetch videos as audio files
2. **Transcribe**: `transcriber.py` uses faster-whisper (preferred) or standard whisper
3. **Summarize**: `summarizer.py` processes transcripts using configurable LLM providers
4. **Store**: `file_manager.py` and `summary_storage.py` handle file operations and metadata

### Key Files
- `main.py`: Orchestrates the entire pipeline, processes `data/videos/*.{mp3,mp4,m4a,webm}`
- `summarizer.py`: **Default uses Google Gemini** - change the `summarize()` method to switch providers
- `prompt.py`: Contains `PROMPT_2` template for Chinese summaries with specific formatting rules
- `file_manager.py`: Handles filename sanitization and truncation for Chinese characters (200 byte limit)

## Development Workflows

### Docker Development
```bash
# Standard development setup
docker compose up -d
docker compose exec app bash
make install  # Downloads yt-dlp + installs Python deps
```

### Processing Commands
```bash
# Download only
make yt-dlp url="YOUTUBE_URL"

# Process existing files in data/videos/
make run

# Download + process in one step
make auto url="YOUTUBE_URL"

# Run Streamlit UI
make streamlit
```

### Testing
```bash
make test  # Runs unittest discover pattern
```

## Project-Specific Patterns

### LLM Provider Switching
The summarizer defaults to Google Gemini. To switch providers, modify the `summarize()` method in `summarizer.py`:
```python
def summarize(self, title, text):
    return self.summarize_with_google_gemini(title, text)  # Default
    # return self.summarize_with_openai(title, text)
    # return self.summarize_with_ollama(title, text)
```

### Chinese Filename Handling
The system specifically handles Chinese video titles with:
- Filename sanitization (removes invalid chars: `[\\/:*?"<>|]`)
- Byte-length truncation (200 bytes max for Linux filesystem compatibility)
- UTF-8 encoding considerations in `file_manager.py`

### Transcription Models
Whisper model size is configurable in `main.py`:
```python
transcriber = Transcriber(model_size="tiny")  # Options: tiny, base, small, medium, large
```

### Output Structure
- Videos download to: `data/videos/`
- Summaries save to: `data/_summarized_YYYYMMDDHHMMSS_title.md`
- The system automatically deletes source video files after processing

### Environment Configuration
Required environment variables (at least one LLM provider):
```bash
OPENAI_API_KEY=your_key
GOOGLE_GEMINI_API_KEY=your_key
# Ollama runs on host.docker.internal:11434 for Docker setup
```

### Prompt Engineering
The `PROMPT_2` template in `prompt.py` is specifically designed for Chinese output with:
- Markdown formatting without code blocks
- English preservation for technical terms
- Structured sections ending with "Insight"
- Specific heading format: `## 1. content` (not numbered lists)

## Integration Points

### Ollama Integration
For local model usage, Ollama communicates via `http://host.docker.internal:11434/api/generate` using the `llama3.2` model. The Docker network configuration enables this host-container communication.

### Streamlit Interface
`streamlit_app.py` provides a web UI that mirrors the CLI workflow, maintaining session state for processing history and progress tracking.

### File Processing
The system uses glob patterns to detect processable files and includes Windows Zone.Identifier cleanup, indicating cross-platform file handling considerations.
