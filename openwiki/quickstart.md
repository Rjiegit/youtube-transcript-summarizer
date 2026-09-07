---
type: quickstart
title: 快速開始與開發導覽
description: 從環境設定、安裝、啟動與測試開始，並依開發任務導向架構、API、持久層與整合文件。
tags: [quickstart, setup, navigation]
verified:
  - by: openwiki/0.4.3
    at: 2026-09-07T14:32:56.222Z
sources:
  - id: openwiki-source-bf5be0c9253ed1d07b502e10
    resource: repo://.githooks/pre-commit
  - id: openwiki-source-e201e686a785f09b6d899f0b
    resource: repo://compose.yaml
  - id: openwiki-source-27a43165fe079c2f44e8c6f5
    resource: repo://frontend/nuxt-showcase/package.json
  - id: openwiki-source-8c08a854bf0339fc3de677b0
    resource: repo://frontend/nuxt-showcase/scripts/check-env.mjs
  - id: openwiki-source-012f2c78e3b1446dfc35803f
    resource: repo://Makefile
  - id: openwiki-source-05ccef8d4cf1698187f20464
    resource: repo://pyproject.toml
  - id: openwiki-source-da418bc01cba89686ece3492
    resource: repo://scripts/install-git-hooks.sh
  - id: openwiki-source-224f65803d3de46b7fae180b
    resource: repo://src/apps/extension/manifest.json
  - id: openwiki-source-48e217db31524d96d35dbecd
    resource: repo://src/apps/extension/options.js
  - id: openwiki-source-0520e948964d45782d02b5a3
    resource: repo://src/apps/extension/service_worker.js
  - id: openwiki-source-526d4ed1a7d9ebdeb9c244a6
    resource: repo://src/core/config.py
  - id: openwiki-source-36d48d46c256392dc902bc2d
    resource: repo://src/infrastructure/llm/model_options.py
  - id: openwiki-source-791a1bcc2cae6ed2d067dedb
    resource: repo://src/infrastructure/llm/weighted_selection.py
  - id: openwiki-source-df04114da62d5e054970a89f
    resource: repo://src/services/pipeline/processing_runner.py
generated: { by: "codex", at: "2026-09-07T14:32:56.222Z" }
---

# 快速開始與開發導覽

這個 repository 包含 Python 3.14 的 YouTube 轉錄/摘要平台、`frontend/nuxt-showcase` 的獨立 Nuxt 3 成果展示站，以及 `src/apps/extension` 的 Chrome/Edge Manifest V3 client。Python 側提供 FastAPI、Streamlit、queue worker 和 RSS monitor；Extension 呼叫 FastAPI；Nuxt server routes 直接讀取 Notion。

## 最短本機啟動路徑

在 repository root：

```bash
cp .env.example .env
uv sync --frozen --no-install-project
make api
```

另開 terminal 啟動 Streamlit：

```bash
make streamlit
```

API 預設為 `http://localhost:8080`，Streamlit 預設為 `http://localhost:8501`。預設自動摘要池目前只有 Gemini，`.env` 請提供 `GOOGLE_GEMINI_API_KEY`。`Config.validate()` 雖接受任一摘要 provider key，但只有 OpenAI 或 Ollama key 仍無法使用目前的預設候選池；實際 pipeline 會寫入 Notion，因此正常處理也需要 `NOTION_API_KEY` 與 `NOTION_DATABASE_ID`。不要提交 `.env`。

建立 task 後 API 通常會自動排程 background worker；也可手動同步 drain SQLite queue：

```bash
make run
```

本機下載另需 PATH 上的 `yt-dlp`；`uv sync` 不會安裝此執行檔。可用 `make yt-dlp-update` 安裝至 `/usr/local/bin/yt-dlp`，該位置可能需要寫入權限。

## Docker 啟動

```bash
docker compose up -d
```

這會啟動 API、Streamlit 與 RSS monitor。API container 啟動時預設更新 yt-dlp；不希望啟動時存取下載來源可在 Compose 載入的 `.env` 設定 `YTDLP_AUTO_UPDATE=0`。RSS monitor 還需 `RSS_MONITOR_ENABLED=true` 才會實際 polling。

## Nuxt Showcase

```bash
cd frontend/nuxt-showcase
npm install
npm run check-env
npm run dev
```

開發站預設在 `http://localhost:3000`。上述直接執行 `npm run dev` 的流程請使用 frontend `.env` 或預先匯出的環境變數。若設定只放在 repository root `.env`，請回 root 執行 `make showcase`，由 Makefile 載入後啟動。`npm run check-env` 自行讀取 root `.env` 的結果不會傳給後續程序。必要設定為 Notion token 與 database id；標準 `NOTION_*` 名稱優先於相容的 `NUXT_*` 名稱。Showcase 是唯讀介面，不會啟動 Python processing pipeline。

## Browser Extension

先啟動 FastAPI，再到 Chrome/Edge 擴充功能頁啟用開發者模式，選擇「載入未封裝項目」並指向：

```text
src/apps/extension
```

Options page 的 API Base URL 預設為 `http://localhost:8080`。Extension 可從 YouTube 影片頁/連結建立 SQLite task，也可從 channel context 建立 RSS subscription；它不包含 worker 或 Notion credentials。

## 驗證變更

每個新 clone 或 checkout 先從 repository root 安裝 Git hooks：

```bash
make install-hooks
```

之後 `git commit` 會自動以 Betterleaks 檢查所有 staged changes；需要在 commit 前手動執行同一檢查時使用 `make betterleaks-staged`。日常 Git 防護不需執行 `betterleaks dir .`，因為 `dir` 會連同未追蹤的本機 `.env` 與工具狀態一起掃描。

在 repository root 執行 Python suite 與 lint：

```bash
make test
uv run flake8 .
```

上述為一般本機檢查；CI 實際採兩階段 lint，完整指令與阻擋條件見[開發規則與測試策略](operations/development-and-testing.md)。

執行 Nuxt suite 與 production build：

```bash
npm --prefix frontend/nuxt-showcase run test
npm --prefix frontend/nuxt-showcase run build
```

## 依任務找文件

| 你要做的事 | 文件 |
| --- | --- |
| 了解元件責任與跨系統資料流 | [系統架構與端到端資料流](architecture/system-overview.md) |
| 盤點 Python/npm/executable/遠端服務依賴 | [模組邊界與外部依賴](architecture/module-boundaries-and-dependencies.md) |
| 修改 API request、status、authentication 或 client | [HTTP API 與 Client 契約](integrations/http-api-and-clients.md) |
| 修改 SQLite/Notion backend、locks 或輸出 artifacts | [任務、鎖與結果持久化](architecture/task-and-result-storage.md) |
| 修改 task API、dedup、retry 或 locks | [任務生命週期與併發控制](workflows/task-lifecycle.md) |
| 修改下載、Whisper、LLM 或輸出 | [媒體轉錄與摘要流程](workflows/media-processing.md) |
| 修改 provider、模型權重或 failover | [LLM Providers、選擇與 Failover](integrations/llm-providers.md) |
| 修改 Chrome/Edge Extension | [Browser Extension 任務與 RSS 入口](integrations/browser-extension.md) |
| 維護 RSS channel automation | [YouTube RSS 自動化](workflows/rss-automation.md) |
| 修改 Notion schema 或 Python/Nuxt 整合 | [Notion 資料整合](integrations/notion-and-showcase.md) |
| 修改 Showcase UX、read state 或 SWR | [Nuxt Showcase 使用體驗與資料快取](integrations/showcase-experience.md) |
| 設定 Docker、env、cache 或部署 | [設定、執行與部署](operations/configuration-and-deployment.md) |
| 新增或定位測試 | [開發規則與測試策略](operations/development-and-testing.md) |

## 常見檢查

- Showcase 顯示缺少設定：先執行 `npm run check-env`，再查看 `/api/showcase/diagnostics`。
- diagnostics 正常但無資料：查看 `/api/showcase/health`，確認 Notion integration 權限、database id 與 status schema。
- task 已 Pending 但未開始：呼叫 `POST /processing-jobs` 或執行 `make run`；先確認是否已有 processing lock。
- Extension 無法送出：確認 Options API Base URL、API connectivity 與頁面是否為支援的 YouTube URL；channel handle 還需要 DOM 提供 channel id。
- RSS 沒有建立舊影片 tasks：首次 poll 只 seed watermark，這是避免回填整個歷史 feed 的預期行為。
