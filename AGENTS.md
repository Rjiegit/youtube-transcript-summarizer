
# Repository Guidelines

## Project Structure & Module Organization
- `apps/whisper_summary/apps/ui/streamlit_app.py`: Streamlit UI entry for local use and Docker。
- Core modules（主要都在 `apps/whisper_summary/`）：
  - `apps/whisper_summary/infrastructure/media/transcription/transcriber.py` (Whisper)
  - `apps/whisper_summary/infrastructure/llm/summarizer_service.py` (LLMs)
  - `apps/whisper_summary/infrastructure/media/downloader.py`
  - `apps/whisper_summary/services/pipeline/processing_runner.py`
  - `apps/whisper_summary/infrastructure/storage/file_storage.py`
  - `apps/whisper_summary/infrastructure/storage/summary_storage.py`
  - `apps/whisper_summary/core/config.py`
- FastAPI：`apps/whisper_summary/apps/api/main.py` 負責 app assembly，feature endpoints 位於 `apps/whisper_summary/apps/api/routers/`，request／response models 位於 `apps/whisper_summary/apps/api/schemas.py`。
- Data & storage: `data/` (inputs/outputs), `apps/whisper_summary/infrastructure/persistence/` (Notion/SQLite adapters), `apps/whisper_summary/domain/interfaces/` (typed interfaces).
- Application-facing repository ports 位於 `apps/whisper_summary/domain/ports/`；concrete adapter 建立集中於 `apps/whisper_summary/infrastructure/*composition.py`。
- Browser Extension: `apps/browser-extension/`（獨立 Manifest V3 client，不放在 Python `apps/whisper_summary/`）。
- Tests: Python unit／integration tests 與 fixtures 位於 `apps/whisper_summary/tests/`；Showcase tests 位於 `apps/showcase/tests/`；跨應用契約 fixture 位於 `contracts/`。
- Tooling: `.github/workflows/main.yml` (CI), `compose.yaml` (Docker services), `apps/whisper_summary/pyproject.toml` + `apps/whisper_summary/uv.lock`, `Makefile`。

## Build, Test, and Development Commands
- Install deps（不含安裝專案本體）: `uv sync --project apps/whisper_summary --frozen --no-install-project`
- Install/Update yt-dlp（會寫入 `/usr/local/bin/yt-dlp`，可能需要權限；Docker 內較常用）: `make install` 或 `make yt-dlp-update`
- Run Streamlit app: `make streamlit`（使用 `apps/whisper_summary/.env`）
- Run API: `make api`
- Run worker CLI（SQLite）: `make run`
- Run dedicated processing worker: `make processing-worker`
- Docker (dev): `docker compose up -d`（或 `make docker-up`）啟動 `streamlit(:8501)` + `api(:8080)`（Makefile 會自動相容 `docker-compose` 舊指令）
- 在 container 中執行指令：`docker compose exec streamlit bash -lc "<COMMAND>"` 或 `docker compose exec api bash -lc "<COMMAND>"`（依要操作的 service 選擇）
- Download a video: `make yt-dlp url="<YOUTUBE_URL>"` → saves under `data/videos/`
- One-shot download+process: `make auto url="<YOUTUBE_URL>"`
- Tests (unittest discovery): `make test`；分類執行使用 `make test-unit` 或 `make test-integration`（避免使用 `python`，有些環境只有 `python3`）
- Lint (CI parity): `make lint`（等同 `uv run --project apps/whisper_summary flake8 --config apps/whisper_summary/.flake8 .`）
- Browser Extension validation: `make extension-check`

## Coding Style & Naming Conventions
- Follow PEP 8; 4-space indentation; prefer type hints.
- Line length: 127 (matches CI’s flake8 config).
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep modules focused; place abstractions in `apps/whisper_summary/domain/interfaces/` and adapters in `apps/whisper_summary/infrastructure/persistence/`.

## Testing Guidelines
- Framework: `unittest` (used in CI). Name tests `test_*.py` (or `test*.py`)；隔離測試放在 `apps/whisper_summary/tests/unit/`，跨 API／component boundary 的測試放在 `apps/whisper_summary/tests/integration/`。
- Aim for fast, isolated unit tests around `transcriber`, `summarizer`, and `processing` logic; mock network/LLM/Notion.
- Run locally: `make test`（或 `PYTHONPATH=apps uv run --project apps/whisper_summary python -m unittest discover -s apps/whisper_summary/tests -t apps -p "test*.py" -v`）.

## Commit & Pull Request Guidelines
- Commits: present-tense, concise subject, optional body. Example: `feat: add Notion status updates in summary_storage`
- PRs: include summary, motivation, screenshots (for UI), repro/steps, and linked issues. Target `master`.
- CI runs flake8 and unittest on push/PR; keep builds green.

### 遠端 Git 寫入必須當次確認
- AI agent 執行任何 `git push` 前，必須先完成修改、驗證與 review，向使用者說明將推送的 commit、remote、branch 及影響，停下來取得當次明確確認後才能執行。
- 此規則涵蓋一般 push、`--force`、`--force-with-lease`、推送／刪除遠端 branch 或 tag，以及透過 API、其他工具或腳本進行的等效遠端 Git 寫入。
- 先前任務的 push 授權不得沿用；「進行開發」、「自行 review」、「全部完成」或授權本機 commit／amend／squash，均不代表允許 push。即使任務一開始要求 push，也必須在具體推送內容可供檢查後，再取得執行前確認。
- Force push 必須額外說明將被改寫的遠端歷史；使用者確認後優先採用 `--force-with-lease`。
- 使用者只要求指令或表示將手動執行時，只提供指令，不得代為執行。確認尚未收到時，不得透過 hook、背景工作或其他方式推送。
- 發布／合併 PR、部署網站等其他遠端發布動作，也須在結果可供檢查後停下來取得當次確認，不得從開發或 review 授權推定。

## Security & Configuration
- Use `apps/whisper_summary/.env` (copy `apps/whisper_summary/.env.example`). Common keys:
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

- Do not enumerate, preload, or search wikis at task start. Use retrieval when the user asks for it, when unfamiliar architecture or dependency behavior materially affects the task, or when source inspection leaves an important uncertainty. Stop once the question is grounded.
- When those conditions apply and OpenWiki retrieval tools are available, use `openwiki_search` for just-in-time context and `openwiki_read` for the relevant complete sections. If search returns `workspace_required`, ask which listed workspace to use and retry with its ID.
- Use `openwiki_list_workspaces` or `openwiki_list_wikis` when workspace membership itself needs to be discovered.
- If the retrieval tools are unavailable, read `openwiki/quickstart.md` and follow its links to the relevant pages.
- Treat source code and tests as authoritative. A brief's unknowns and review items are verification gaps, not automatic requirements.
- Prefer the narrowest quiet validation that proves the changed behavior. Preserve complete failure output.

The scheduled OpenWiki GitHub Actions workflow refreshes the repository wiki. Do not hand-edit generated OpenWiki pages unless explicitly asked; prefer updating source code/docs and letting OpenWiki regenerate.

<!-- OPENWIKI:END -->
