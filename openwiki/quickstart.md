---
type: quickstart
title: 快速開始與開發導覽
description: 從環境設定、安裝、啟動與測試開始，並依開發任務導向架構、API、持久層與整合文件。
tags: [quickstart, setup, navigation]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-31T13:03:19.622Z
sources:
  - id: openwiki-source-e201e686a785f09b6d899f0b
    resource: repo://compose.yaml
  - id: openwiki-source-27a43165fe079c2f44e8c6f5
    resource: repo://frontend/nuxt-showcase/package.json
  - id: openwiki-source-012f2c78e3b1446dfc35803f
    resource: repo://Makefile
  - id: openwiki-source-05ccef8d4cf1698187f20464
    resource: repo://pyproject.toml
  - id: openwiki-source-224f65803d3de46b7fae180b
    resource: repo://src/apps/extension/manifest.json
  - id: openwiki-source-48e217db31524d96d35dbecd
    resource: repo://src/apps/extension/options.js
  - id: openwiki-source-0520e948964d45782d02b5a3
    resource: repo://src/apps/extension/service_worker.js
  - id: openwiki-source-526d4ed1a7d9ebdeb9c244a6
    resource: repo://src/core/config.py
generated: { by: "codex", at: "2026-08-31T13:03:19.622Z" }
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

API 預設為 `http://localhost:8080`，Streamlit 預設為 `http://localhost:8501`。`.env` 至少提供一個可用的摘要 provider key；實際 pipeline 會寫入 Notion，因此正常處理也需要 `NOTION_API_KEY` 與 `NOTION_DATABASE_ID`。不要提交 `.env`。

建立 task 後 API 通常會自動排程 background worker；也可手動同步 drain SQLite queue：

```bash
make run
```

## Docker 啟動

```bash
docker compose up -d
```

這會啟動 API、Streamlit 與 RSS monitor。API container 啟動時預設更新 yt-dlp；不希望啟動時存取下載來源可設定 `YTDLP_AUTO_UPDATE=0`。RSS monitor 還需 `RSS_MONITOR_ENABLED=true` 才會實際 polling。

## Nuxt Showcase

```bash
cd frontend/nuxt-showcase
npm install
npm run check-env
npm run dev
```

開發站預設在 `http://localhost:3000`。必要設定為 Notion token 與 database id，可放在 frontend `.env` 或 repository root `.env`；標準 `NOTION_*` 名稱優先於相容的 `NUXT_*` 名稱。Showcase 是唯讀介面，不會啟動 Python processing pipeline。

## Browser Extension

先啟動 FastAPI，再到 Chrome/Edge 擴充功能頁啟用開發者模式，選擇「載入未封裝項目」並指向：

```text
src/apps/extension
```

Options page 的 API Base URL 預設為 `http://localhost:8080`。Extension可從YouTube影片頁/連結建立SQLite task，也可從channel context建立RSS subscription；它不包含worker或Notion credentials。

## 驗證變更

在 repository root 執行 Python suite 與 lint：

```bash
make test
uv run flake8 .
```

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
| 修改 API request、status、authentication 或 client | [HTTP API 與 Client 契約](interfaces/http-api-and-clients.md) |
| 修改 SQLite/Notion backend、locks 或輸出 artifacts | [任務、鎖與結果持久化](persistence/task-and-result-storage.md) |
| 修改 task API、dedup、retry 或 locks | [任務生命週期與併發控制](workflows/task-lifecycle.md) |
| 修改下載、Whisper、LLM 或輸出 | [媒體轉錄與摘要流程](workflows/media-processing.md) |
| 修改 provider、模型權重或 failover | [LLM Providers、選擇與 Failover](integrations/llm-providers.md) |
| 修改 Chrome/Edge Extension | [Browser Extension 任務與 RSS 入口](integrations/browser-extension.md) |
| 維護 RSS channel automation | [YouTube RSS 自動化](integrations/rss-automation.md) |
| 修改 Notion schema 或 Python/Nuxt 整合 | [Notion 資料整合](integrations/notion-and-showcase.md) |
| 修改 Showcase UX、read state 或 SWR | [Nuxt Showcase 使用體驗與資料快取](frontend/showcase-experience.md) |
| 設定 Docker、env、cache 或部署 | [設定、執行與部署](operations/configuration-and-deployment.md) |
| 新增或定位測試 | [測試策略與擴充指南](testing/test-strategy.md) |

## 常見檢查

- Showcase 顯示缺少設定：先執行 `npm run check-env`，再查看 `/api/showcase/diagnostics`。
- diagnostics 正常但無資料：查看 `/api/showcase/health`，確認 Notion integration 權限、database id 與 status schema。
- task 已 Pending 但未開始：呼叫 `POST /processing-jobs` 或執行 `make run`；先確認是否已有 processing lock。
- Extension 無法送出：確認 Options API Base URL、API connectivity與頁面是否為支援的YouTube URL；channel handle還需要DOM提供channel id。
- RSS 沒有建立舊影片 tasks：首次 poll 只 seed watermark，這是避免回填整個歷史 feed 的預期行為。
