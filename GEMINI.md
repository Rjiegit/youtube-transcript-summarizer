# Gemini Project Brief: youtube-transcript-summarizer

## 1. Project Overview

This project is a Python-based application that downloads YouTube video transcripts, summarizes them using a large language model, and provides the summary to the user. The main user interface is built with Streamlit.

## 2. Technical Stack

- **Language:** Python 3.10+
- **Main Libraries:**
  - `streamlit`: For the web interface.
  - `fastapi`: For building the API.
  - `pytube`: For downloading YouTube videos.
  - `openai`: For accessing summarization models.
  - `pytest`: For unit testing.
- **Dependency Management:** `pip` with `requirements.txt`.

## 3. Key Commands

- **Install Dependencies:** `pip install -r requirements.txt`
- **Run the App:** `streamlit run src/apps/ui/streamlit_app.py`
- **Run Tests:** `python -m unittest -v`
- **Check Style:** `flake8 .`
- **Format Code:** `ruff format .`

## 4. Coding Conventions

- **Style Guide:** Follows PEP 8. Use `ruff` to enforce.
- **Naming:** Use `snake_case` for variables and functions. Use `PascalCase` for classes.
- **Typing:** All new functions and methods must include type hints.
- **Docstrings:** Use Google-style docstrings for all public modules and functions.

## 5. Architectural Patterns

- **Separation of Concerns:**
  - `src/infrastructure/media/transcription/transcriber.py`: Handles video transcription logic.
  - `src/infrastructure/llm/summarizer_service.py`: Handles text summarization logic.
  - `src/apps/ui/streamlit_app.py`: Contains all UI-related code (invoked via root wrapper).
  - `src/infrastructure/media/downloader.py`: Manages downloading video content.
- **Error Handling:** Use custom exceptions for specific application errors (e.g., `InvalidURLError`, `DownloadError`).

## 6. Specific Rules & Constraints

- Do not commit secrets or API keys to the repository. Use environment variables loaded from a `.env` file.
- All user-facing text in the Streamlit app should be clear and concise.
- When adding new dependencies, update `requirements.txt` and `docker-compose.yaml` accordingly.
