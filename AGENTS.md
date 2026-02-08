
# Repository Guidelines

## Project Structure & Module Organization
- `src/apps/ui/streamlit_app.py`: Streamlit UI entry for local use and Docker。
- Core modules（主要都在 `src/`）：
  - `src/infrastructure/media/transcription/transcriber.py` (Whisper)
  - `src/infrastructure/llm/summarizer_service.py` (LLMs)
  - `src/infrastructure/media/downloader.py`
  - `src/services/pipeline/processing_runner.py`
  - `src/infrastructure/storage/file_storage.py`
  - `src/infrastructure/storage/summary_storage.py`
  - `src/core/config.py`
- Data & storage: `data/` (inputs/outputs), `src/infrastructure/persistence/` (Notion/SQLite adapters), `src/domain/interfaces/` (typed interfaces).
- Tooling: `.github/workflows/main.yml` (CI), `compose.yaml` (Docker services), `pyproject.toml` + `uv.lock`, `Makefile`, `openspec/`（規格與變更提案）。

## Build, Test, and Development Commands
- Install deps（不含安裝專案本體）: `uv sync --frozen --no-install-project`
- Install/Update yt-dlp（會寫入 `/usr/local/bin/yt-dlp`，可能需要權限；Docker 內較常用）: `make install` 或 `make yt-dlp-update`
- Run Streamlit app: `make streamlit`（等同 `uv run streamlit run src/apps/ui/streamlit_app.py`）
- Run API: `make api`
- Run worker CLI（SQLite）: `make run`
- Docker (dev): `docker compose up -d`（或 `make docker-up`）啟動 `streamlit(:8501)` + `api(:8080)`（Makefile 會自動相容 `docker-compose` 舊指令）
- 在 container 中執行指令：`docker compose exec streamlit bash -lc "<COMMAND>"` 或 `docker compose exec api bash -lc "<COMMAND>"`（依要操作的 service 選擇）
- Download a video: `make yt-dlp url="<YOUTUBE_URL>"` → saves under `data/videos/`
- One-shot download+process: `make auto url="<YOUTUBE_URL>"`
- Tests (unittest discovery): `make test` 或 `uv run python -m unittest discover -s . -p "test*.py" -v`（避免使用 `python`，有些環境只有 `python3`）
- Lint (CI parity): `uv run flake8 .`（避免直接跑 `flake8 .`，可能不在 PATH）

## Coding Style & Naming Conventions
- Follow PEP 8; 4-space indentation; prefer type hints.
- Line length: 127 (matches CI’s flake8 config).
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep modules focused; place abstractions in `interfaces/` and adapters in `database/`.

## Testing Guidelines
- Framework: `unittest` (used in CI). Name tests `test_*.py` (or `test*.py`) beside the code or under a `tests/` folder.
- Aim for fast, isolated unit tests around `transcriber`, `summarizer`, and `processing` logic; mock network/LLM/Notion.
- Run locally: `make test`（或 `uv run python -m unittest discover -s . -p "test*.py" -v`）.

## Commit & Pull Request Guidelines
- Commits: present-tense, concise subject, optional body. Example: `feat: add Notion status updates in summary_storage`
- PRs: include summary, motivation, screenshots (for UI), repro/steps, and linked issues. Target `master`.
- CI runs flake8 and unittest on push/PR; keep builds green.

## Security & Configuration
- Use `.env` (copy `.env.example`). Common keys:
  - LLM: `OPENAI_API_KEY`, `GOOGLE_GEMINI_API_KEY`
  - Notion: `NOTION_API_KEY`, `NOTION_DATABASE_ID`, `NOTION_URL`
  - Ops/Integrations: `DISCORD_WEBHOOK_URL`, `PROCESSING_LOCK_ADMIN_TOKEN`, `TASK_CACHE_TTL_SECONDS`
- Never commit secrets; validate via `config.py` and keep fallbacks sensible.
- Large downloads and outputs live in `data/`; avoid committing generated artifacts.

# Communication Guideline
Please use Traditional Chinese (Taiwan) as the primary language for communication and documentation. Technical terms can be kept in English. English explanations may be provided when necessary.

## Notes
- Primary UX is via Streamlit; CLI/cron entry points may vary. When adding new entry scripts, document them in the README and wire Makefile targets accordingly.

## Active Technologies
- Python 3.14 + Streamlit, FastAPI backend responses consumed by UI, Notion storage integration (existing), requests/HTTP client for API data (001-notion-url-list)
- 檔案輸出 (Markdown summaries) + Notion（已有 URL 來源）；無新增持久層 (001-notion-url-list)

## Recent Changes
- 001-notion-url-list: Added Python 3.14 + Streamlit, FastAPI backend responses consumed by UI, Notion storage integration (existing), requests/HTTP client for API data
