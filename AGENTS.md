
# Repository Guidelines

## Project Structure & Module Organization
- `whisper_summary/apps/ui/streamlit_app.py`: Streamlit UI entry for local use and Docker。
- Core modules（主要都在 `whisper_summary/`）：
  - `whisper_summary/infrastructure/media/transcription/transcriber.py` (Whisper)
  - `whisper_summary/infrastructure/llm/summarizer_service.py` (LLMs)
  - `whisper_summary/infrastructure/media/downloader.py`
  - `whisper_summary/services/pipeline/processing_runner.py`
  - `whisper_summary/infrastructure/storage/file_storage.py`
  - `whisper_summary/infrastructure/storage/summary_storage.py`
  - `whisper_summary/core/config.py`
- FastAPI：`whisper_summary/apps/api/main.py` 負責 app assembly，feature endpoints 位於 `whisper_summary/apps/api/routers/`，request／response models 位於 `whisper_summary/apps/api/schemas.py`。
- Data & storage: `data/` (inputs/outputs), `whisper_summary/infrastructure/persistence/` (Notion/SQLite adapters), `whisper_summary/domain/interfaces/` (typed interfaces).
- Application-facing repository ports 位於 `whisper_summary/domain/ports/`；concrete adapter 建立集中於 `whisper_summary/infrastructure/*composition.py`。
- Browser Extension: `apps/browser-extension/`（獨立 Manifest V3 client，不放在 Python `whisper_summary/`）。
- Tooling: `.github/workflows/main.yml` (CI), `compose.yaml` (Docker services), `pyproject.toml` + `uv.lock`, `Makefile`, `openspec/`（規格與變更提案）。

## Build, Test, and Development Commands
- Install deps（不含安裝專案本體）: `uv sync --frozen --no-install-project`
- Install/Update yt-dlp（會寫入 `/usr/local/bin/yt-dlp`，可能需要權限；Docker 內較常用）: `make install` 或 `make yt-dlp-update`
- Run Streamlit app: `make streamlit`（等同 `uv run streamlit run whisper_summary/apps/ui/streamlit_app.py`）
- Run API: `make api`
- Run worker CLI（SQLite）: `make run`
- Run dedicated processing worker: `make processing-worker`
- Docker (dev): `docker compose up -d`（或 `make docker-up`）啟動 `streamlit(:8501)` + `api(:8080)`（Makefile 會自動相容 `docker-compose` 舊指令）
- 在 container 中執行指令：`docker compose exec streamlit bash -lc "<COMMAND>"` 或 `docker compose exec api bash -lc "<COMMAND>"`（依要操作的 service 選擇）
- Download a video: `make yt-dlp url="<YOUTUBE_URL>"` → saves under `data/videos/`
- One-shot download+process: `make auto url="<YOUTUBE_URL>"`
- Tests (unittest discovery): `make test`；分類執行使用 `make test-unit` 或 `make test-integration`（避免使用 `python`，有些環境只有 `python3`）
- Lint (CI parity): `uv run flake8 .`（避免直接跑 `flake8 .`，可能不在 PATH）
- Browser Extension validation: `make extension-check`

## Coding Style & Naming Conventions
- Follow PEP 8; 4-space indentation; prefer type hints.
- Line length: 127 (matches CI’s flake8 config).
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep modules focused; place abstractions in `whisper_summary/domain/interfaces/` and adapters in `whisper_summary/infrastructure/persistence/`.

## Testing Guidelines
- Framework: `unittest` (used in CI). Name tests `test_*.py` (or `test*.py`)；隔離測試放在 `tests/unit/`，跨 API／component boundary 的測試放在 `tests/integration/`。
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
- Human-facing development conventions are summarized in `CONTRIBUTING.md`; keep it aligned with these repository guidelines.
- Primary UX is via Streamlit; CLI/cron entry points may vary. When adding new entry scripts, document them in the README and wire Makefile targets accordingly.

<!-- OPENWIKI:START -->

## OpenWiki

This repository has a generated `openwiki/` evidence index. It is optional just-in-time context, not required startup reading.

- Treat source code and tests as authoritative. A brief's unknowns and review items are verification gaps, not automatic requirements.
- Prefer the narrowest quiet validation that proves the changed behavior. Preserve complete failure output.

The scheduled OpenWiki GitHub Actions workflow refreshes the repository wiki. Do not hand-edit generated OpenWiki pages unless explicitly asked; prefer updating source code/docs and letting OpenWiki regenerate.

<!-- OPENWIKI:END -->
