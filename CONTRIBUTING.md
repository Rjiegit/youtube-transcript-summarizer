# 開發貢獻指南

本文件是人類開發者的日常協作入口。實際系統行為以原始碼與測試為準；架構與流程請參考 `openwiki/`，AI agent 的 repository 指引則以 `AGENTS.md` 為準。

## 開發環境

```bash
cp .env.example .env
uv sync --frozen --no-install-project
make install-hooks
```

常用入口：

```bash
make api
make streamlit
make run
make rss-monitor
```

Docker 開發環境使用：

```bash
docker compose up -d
```

## 程式碼編排

- `src/domain/`：domain models 與 typed interfaces，不放第三方服務實作。
- `src/services/`：use case 與流程 orchestration。
- `src/infrastructure/`：LLM、媒體、通知、儲存與 persistence adapters。
- `src/apps/`：FastAPI、Streamlit、CLI 與 RSS monitor 等 Python 入口。
- `apps/browser-extension/`：獨立 Chrome／Edge Manifest V3 client。
- `frontend/nuxt-showcase/`：獨立 Nuxt 3 成果展示站。

新增抽象時放在 `src/domain/interfaces/`；SQLite、Notion 等 adapter 放在 `src/infrastructure/persistence/`。入口只負責輸入輸出與 use case 組裝，主要流程應留在 service 層。

## Python 風格

- 遵循 PEP 8，使用 4 spaces indentation。
- 單行上限 127 字元，與 CI flake8 設定一致。
- 函式與變數使用 `snake_case`，類別使用 `PascalCase`，常數使用 `UPPER_SNAKE_CASE`。
- 新增或修改的公開介面優先補上 type hints。
- 保持模組與函式聚焦，不為未發生的需求預先建立抽象。

Nuxt 的 TypeScript、Vue、測試與命名規則請遵循 `frontend/nuxt-showcase/AGENTS.md`。

Browser Extension 不屬於 Python package。修改後需確認 `manifest.json` 引用的檔案存在、JavaScript 語法有效，並以瀏覽器 Load unpacked 驗證主要互動。

## 測試與驗證

Python 測試使用 `unittest`：

```bash
make test
uv run flake8 .
```

測試檔命名為 `test*.py`，放在 `tests/` 對應的 unit 或 integration 範圍。優先撰寫快速、隔離的單元測試；網路、LLM、Notion、Discord 與 yt-dlp 等外部邊界應使用 mock、fake 或 fixture。

Nuxt 驗證：

```bash
npm --prefix frontend/nuxt-showcase run test
npm --prefix frontend/nuxt-showcase run build
```

提交前執行與變更風險相符的最小完整驗證；完整測試策略見 `openwiki/testing/test-strategy.md`。

## Secrets 與本機資料

- 使用 `.env` 提供 credential，禁止提交 API keys、tokens 或 cookies。
- 第一次 clone 後執行 `make install-hooks`。
- 手動掃描 staged changes 可使用 `make betterleaks-staged`。
- `data/` 用於下載、轉錄與摘要產物，不應提交 generated artifacts。
- 不要用 `betterleaks dir .` 取代 staged scan；它可能讀取未追蹤的本機 credential。

## Commit 與 Pull Request

- Commit subject 使用簡短、現在式描述，例如 `feat: add task retry guard`。
- 一個 commit 聚焦一個主要意圖。
- Pull Request 應包含摘要、動機、驗證結果、相關 issue；UI 變更另附畫面。
- 目標分支為 `master`，送出前保持相關測試與 lint 綠燈。

## 文件維護

- 使用者可見的啟動或操作方式改變時，更新 `readme.md` 與相關 Makefile target。
- 架構或流程改變時，透過 OpenWiki 更新流程重新產生 `openwiki/`；不要直接修改其 generated indexes、Claims 或 metadata。
- 功能提案、需求與設計決策放在 `openspec/`。
- 過期設計只能保留為明確標示的歷史文件，不應繼續描述成目前待辦。
