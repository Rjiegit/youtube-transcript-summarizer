# Repository Guidelines

## Project Structure & Module Organization
- `streamlit_app.py`: Streamlit UI entry for local use and Docker.
- Core modules: `transcriber.py` (Whisper), `summarizer.py` (LLMs), `youtube_downloader.py`, `processing.py`, `file_manager.py`, `summary_storage.py`, `config.py`.
- Data & storage: `data/` (inputs/outputs), `database/` (Notion/SQLite adapters), `interfaces/` (typed interfaces).
- Tooling: `.github/workflows/main.yml` (CI), `compose.yaml` (Docker services), `requirements.txt`, `Makefile`.

## Build, Test, and Development Commands
- Install deps and yt-dlp: `make install`
- Run Streamlit app: `make streamlit` (or `streamlit run streamlit_app.py`)
- Docker (dev): `docker compose up -d` to start the app on `:8501`
- Download a video: `make yt-dlp url="<YOUTUBE_URL>"` → saves under `data/videos/`
- One-shot download+process: `make auto url="<YOUTUBE_URL>"`
- Tests (unittest discovery): `make test` or `python -m unittest discover -s . -p "test*.py" -v`
- Lint (CI parity): `flake8 .`

## Coding Style & Naming Conventions
- Follow PEP 8; 4-space indentation; prefer type hints.
- Line length: 127 (matches CI’s flake8 config).
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep modules focused; place abstractions in `interfaces/` and adapters in `database/`.

## Testing Guidelines
- Framework: `unittest` (used in CI). Name tests `test_*.py` (or `test*.py`) beside the code or under a `tests/` folder.
- Aim for fast, isolated unit tests around `transcriber`, `summarizer`, and `processing` logic; mock network/LLM/Notion.
- Run locally: `python -m unittest -v`.

## Commit & Pull Request Guidelines
- Commits: present-tense, concise subject, optional body. Example: `feat: add Notion status updates in summary_storage`
- PRs: include summary, motivation, screenshots (for UI), repro/steps, and linked issues. Target `master`.
- CI runs flake8 and unittest on push/PR; keep builds green.

## Security & Configuration
- Use `.env` (copy `.env.example`). Common keys: `OPENAI_API_KEY`, `GOOGLE_GEMINI_API_KEY`, `NOTION_API_KEY`, `NOTION_DATABASE_ID`.
- Never commit secrets; validate via `config.py` and keep fallbacks sensible.
- Large downloads and outputs live in `data/`; avoid committing generated artifacts.

# Communication Guideline
Please use Traditional Chinese (Taiwan) as the primary language for communication and documentation. Technical terms can be kept in English. English explanations may be provided when necessary.

## Notes
- Primary UX is via Streamlit; CLI/cron entry points may vary. When adding new entry scripts, document them in the README and wire Makefile targets accordingly.
