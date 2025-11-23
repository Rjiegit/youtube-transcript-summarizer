<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# Repository Guidelines

## Project Structure & Module Organization
- `src/apps/ui/streamlit_app.py`: Streamlit UI entry for local use and Docker。
- Core modules（皆位於 `src/`）：
  - `infrastructure/media/transcription/transcriber.py` (Whisper)
  - `infrastructure/llm/summarizer_service.py` (LLMs)
  - `infrastructure/media/downloader.py`
  - `services/pipeline/processing_runner.py`
  - `infrastructure/storage/file_storage.py`
  - `infrastructure/storage/summary_storage.py`
  - `core/config.py`
- Data & storage: `data/` (inputs/outputs), `src/infrastructure/persistence/` (Notion/SQLite adapters), `src/domain/interfaces/` (typed interfaces).
- Tooling: `.github/workflows/main.yml` (CI), `compose.yaml` (Docker services), `requirements.txt`, `Makefile`.

## Build, Test, and Development Commands
- Install deps and yt-dlp: `make install`
- Run Streamlit app: `make streamlit`（等同 `streamlit run src/apps/ui/streamlit_app.py`，若需保持相容亦可 `streamlit run streamlit_app.py`）
- Docker (dev): `docker compose up -d` to start the app on `:8501`
- 在 container 中執行指令：`docker compose exec app bash -lc "<COMMAND>"`（會在 `app` service 的 bash shell 內執行，適合需要 container 環境的工具）
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
