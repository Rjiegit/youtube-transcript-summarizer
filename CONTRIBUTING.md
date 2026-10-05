# 開發貢獻指南

本文件是人類開發者的日常協作入口。實際系統行為以原始碼與測試為準；架構與流程請參考 `openwiki/`，AI agent 的 repository 指引則以 `AGENTS.md` 為準。

## 開發環境

```bash
cp apps/whisper_summary/.env.example apps/whisper_summary/.env
uv sync --project apps/whisper_summary --frozen --no-install-project
make install-hooks
```

常用入口：

```bash
make api
make streamlit
make run
make processing-worker
make rss-monitor
```

Docker 開發環境使用：

```bash
docker compose up -d
```

`processing-worker` 必須透過 `TASK_API_BASE_URL` claim task lease，不應直接繞過 API
操作 queue。Docker 與本機 worker 可同時執行；新增 worker entrypoint 時必須使用唯一
instance ID、定期 heartbeat，並以 lease token 保護 progress／complete／fail 更新。

## 程式碼編排

- `apps/whisper_summary/domain/`：domain models 與 typed interfaces，不放第三方服務實作。
- `apps/whisper_summary/services/`：use case 與流程 orchestration。
- `apps/whisper_summary/infrastructure/`：LLM、媒體、通知、儲存與 persistence adapters。
- `apps/whisper_summary/apps/`：FastAPI、Streamlit、CLI 與 RSS monitor 等 Python 入口。
- `apps/whisper_summary/tests/`：Python unit／integration tests 與 fixtures。
- `apps/browser-extension/`：獨立 Chrome／Edge Manifest V3 client。
- `apps/showcase/`：獨立 Nuxt 3 成果展示站。
- `contracts/`：Python writer 與 Showcase reader 共用的契約 fixture。

Python package 位於 `apps/whisper_summary/`，import 名稱仍是 `whisper_summary`。
Python 專案設定與 `.env` 也位於同一目錄。從 repository root 手動執行 Python 模組或測試時，
使用 `uv run --project apps/whisper_summary` 與 `PYTHONPATH=apps`；Makefile、Docker image 與 CI 已設定。

新增抽象時放在 `apps/whisper_summary/domain/interfaces/`；SQLite、Notion 等 adapter 放在 `apps/whisper_summary/infrastructure/persistence/`。入口只負責輸入輸出與 use case 組裝，主要流程應留在 service 層。

Processing pipeline 的具體操作集中在 `services/pipeline/engines.py`，legacy 與
LangGraph engine 必須重用相同 operations。新增或調整 pipeline 步驟時，需同步更新
兩個 engine 的 parity test，避免切換後出現外部行為差異。

## Python 風格

- 遵循 PEP 8，使用 4 spaces indentation。
- 單行上限 127 字元，與 CI flake8 設定一致。
- 函式與變數使用 `snake_case`，類別使用 `PascalCase`，常數使用 `UPPER_SNAKE_CASE`。
- 新增或修改的公開介面優先補上 type hints。
- 保持模組與函式聚焦，不為未發生的需求預先建立抽象。

Nuxt 的 TypeScript、Vue、測試與命名規則請遵循 `apps/showcase/AGENTS.md`。

Browser Extension 不屬於 Python package。修改後需確認 `manifest.json` 引用的檔案存在、JavaScript 語法有效，並以瀏覽器 Load unpacked 驗證主要互動。
可先執行 `make extension-check` 完成自動化檢查。

## 測試與驗證

Python 測試使用 `unittest`：

```bash
make test
make test-unit
make test-integration
make lint
```

測試檔命名為 `test*.py`，放在 `apps/whisper_summary/tests/` 對應的 unit 或 integration 範圍。優先撰寫快速、隔離的單元測試；網路、LLM、Notion、Discord 與 yt-dlp 等外部邊界應使用 mock、fake 或 fixture。

Nuxt 驗證：

```bash
npm --prefix apps/showcase run test
npm --prefix apps/showcase run build
```

提交前執行與變更風險相符的最小完整驗證；完整測試策略見 `openwiki/testing/test-strategy.md`。

## Secrets 與本機資料

- 使用 `apps/whisper_summary/.env` 提供 Python app 的 credential，禁止提交 API keys、tokens 或 cookies。
- 第一次 clone 後執行 `make install-hooks`。
- 手動掃描 staged changes 可使用 `make betterleaks-staged`。
- `data/` 用於下載、轉錄與摘要產物，不應提交 generated artifacts。
- 不要用 `betterleaks dir .` 取代 staged scan；它可能讀取未追蹤的本機 credential。

## Commit 與 Pull Request

AI agent 的遠端 Git 寫入與發布流程依 [AGENTS.md](AGENTS.md) 的「遠端 Git 寫入必須當次確認」規則：先完成修改、驗證與 review，提供具體推送內容，再停下來取得使用者當次確認。先前授權或本機 commit／amend／squash 授權不得視為 push 許可；只要求指令時不得代為執行。

- Commit subject 使用簡短、現在式描述，例如 `feat: add task retry guard`。
- 一個 commit 聚焦一個主要意圖。
- Pull Request 應包含摘要、動機、驗證結果、相關 issue；UI 變更另附畫面。
- 目標分支為 `master`，送出前保持相關測試與 lint 綠燈。

## 文件維護

- 使用者可見的啟動或操作方式改變時，更新 `readme.md` 與相關 Makefile target。
- 架構或流程改變時，透過 OpenWiki 更新流程重新產生 `openwiki/`；不要直接修改其 generated indexes、Claims 或 metadata。
- 功能需求與設計決策記錄在對應的 issue 或 Pull Request；持續有效的操作與開發規則同步更新正式文件。
- 過期設計只能保留為明確標示的歷史文件，不應繼續描述成目前待辦。
