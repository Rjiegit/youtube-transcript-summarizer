# Project Context

## Purpose
- 建立一套面向內容創作者與研究者的自動化流程，完成 YouTube 影片下載、音訊擷取、Whisper 轉錄與 LLM 摘要。
- 提供 Streamlit UI 與 FastAPI 介面，支援互動式操作、排程工作與背景批次處理。
- 透過 Markdown 與 Notion 整合將摘要結果結構化保存，方便後續整理與分享。

## Tech Stack
- Python 3.11（Docker `python:3.11-slim` 基底映像）
- Streamlit 作為前端介面
- FastAPI 建置 HTTP API 與背景任務入口
- `faster-whisper`/CT2 執行 Whisper 推論
- yt-dlp 下載 YouTube 影音
- LLM 供應商：OpenAI、Google Gemini，並可選擇 Ollama 本地模型
- SQLite 與 Notion 作為摘要儲存後端
- Docker Compose 管理 app/scheduler 服務

## Project Conventions

### Code Style
- 遵循 PEP 8，4 空白縮排，偏好撰寫 type hints。
- 保持單行長度在 127 字元內（與 flake8 設定一致）。
- 命名採用 `snake_case`（函式/變數）、`PascalCase`（類別）、`UPPER_SNAKE_CASE`（常數）。
- 優先撰寫易讀函式，針對複雜流程再補充精簡註解。

### Architecture Patterns
- 模組化管線：`youtube_downloader` → `transcriber` → `summarizer` → `processing` 與 `file_manager` 協作輸出 Markdown。
- `summarizer` 抽象出多種 LLM 供應商，藉由設定檔與 prompt 模組切換。
- `summary_storage` 以介面模式串接 Notion/SQLite，確保儲存層獨立。
- Streamlit 與 FastAPI 共用核心模組，透過 Docker 服務劃分互動 UI 與排程背景工作。

### Testing Strategy
- 使用 `unittest` 為主要框架，測試檔命名 `test_*.py` 並置於根目錄或 `tests/`。
- 以 `python -m unittest -v` 或 `make test` 執行；CI 亦跑相同指令。
- 側重於單元測試，對外部 API（LLM、Notion、yt-dlp）採用模擬或假資料，以確保離線可重現。
- 新增行為時補齊回歸測試，避免破壞既有轉錄與摘要流程。

### Git Workflow
- 預設以 `master` 為主幹，功能分支合併前提交 Pull Request。
- Commit 訊息採現在式簡潔句首，建議使用 `feat: ...`、`fix: ...` 等慣例前綴。
- PR 需附帶摘要、動機、測試結果與相關截圖（若涉及 UI）。
- 確保 `flake8 .` 與 `python -m unittest` 皆通過再進行合併。

## Domain Context
- 主要服務 YouTube 影音內容的轉錄與摘要，產出偏重繁體中文閱讀體驗。
- 摘要輸出為 Markdown，含關鍵整理、段落標題與洞見，便於知識管理。
- 系統內含 FastAPI 任務佇列端點，可排程批次處理並與 Notion 同步。
- `data/` 底下保存影音、音訊與摘要，`database/` 內含 Notion/SQLite adapter。

## Important Constraints
- `.env` 管理 `OPENAI_API_KEY`、`GOOGLE_GEMINI_API_KEY`、`NOTION_API_KEY` 等敏感資訊，禁止提交到版本控制。
- 大型下載檔案、處理結果統一存放於 `data/`，避免進入 Git。
- 依賴 `ffmpeg`、`yt-dlp` 等系統工具，須在 Docker 或開發環境中預先安裝。
- 維持 Traditional Chinese 介面與說明，以符合目標使用者。

## External Dependencies
- YouTube 平台（透過 yt-dlp 抽取影音/音訊）。
- OpenAI Whisper/faster-whisper 模型權重。
- LLM 供應：OpenAI API、Google Gemini API、Ollama（可選離線）。
- Notion API 與 SQLite 資料庫做為摘要儲存管道。
