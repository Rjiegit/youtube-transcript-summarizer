---
type: quickstart
title: 快速開始與開發導覽
description: 從環境設定、安裝、啟動與測試開始，並依開發任務導向架構、API、持久層與整合文件。
tags: [quickstart, setup, navigation]
sources:
  - id: openwiki-source-bf5be0c9253ed1d07b502e10
    resource: repo://.githooks/pre-commit
  - id: openwiki-source-fd915a0411f41f59671049a8
    resource: repo://apps/browser-extension/manifest.json
  - id: openwiki-source-7f09da405ad8b6929dbd0daf
    resource: repo://apps/browser-extension/options.js
  - id: openwiki-source-3f302af29bc8e91334af86aa
    resource: repo://apps/browser-extension/service_worker.js
  - id: openwiki-source-bb92958ed21ee9cf0accb45d
    resource: repo://apps/showcase/components/ReadSyncControl.vue
  - id: openwiki-source-bbc421d322d74564a269df19
    resource: repo://apps/showcase/package.json
  - id: openwiki-source-36cce2c34e32cbad2ec20271
    resource: repo://apps/showcase/pages/settings/sync.vue
  - id: openwiki-source-6b47ec2bb946dbfe3f605cea
    resource: repo://apps/showcase/README.md
  - id: openwiki-source-62d27fea7294b39bcb77aae5
    resource: repo://apps/showcase/scripts/build-weekly-insights.mjs
  - id: openwiki-source-d2d7610281b3f0057b9f9314
    resource: repo://apps/showcase/scripts/check-env.mjs
  - id: openwiki-source-3b0efe03f5b86982327fa144
    resource: repo://apps/showcase/server/utils/read-sync-config.ts
  - id: openwiki-source-8a8f27feb31a478f83017412
    resource: repo://apps/whisper_summary/apps/api/routers/processing.py
  - id: openwiki-source-3510ac90ffbd030c0a1f2f0d
    resource: repo://apps/whisper_summary/apps/workers/cli.py
  - id: openwiki-source-fb3a71308a5a59482c2767f3
    resource: repo://apps/whisper_summary/apps/workers/processing_worker.py
  - id: openwiki-source-445a1c8f48d3b2e4f898d6be
    resource: repo://apps/whisper_summary/core/config.py
  - id: openwiki-source-cd3c19edb3412c855091bcd0
    resource: repo://apps/whisper_summary/infrastructure/llm/model_options.py
  - id: openwiki-source-25d6d487d3ae6567d7b0397b
    resource: repo://apps/whisper_summary/infrastructure/llm/weighted_selection.py
  - id: openwiki-source-44f784ddceb054f0c06a5950
    resource: repo://apps/whisper_summary/pyproject.toml
  - id: openwiki-source-5d30f93453a5fc9227aa0b47
    resource: repo://apps/whisper_summary/services/pipeline/processing_runner.py
  - id: openwiki-source-e201e686a785f09b6d899f0b
    resource: repo://compose.yaml
  - id: openwiki-source-012f2c78e3b1446dfc35803f
    resource: repo://Makefile
  - id: openwiki-source-da418bc01cba89686ece3492
    resource: repo://scripts/install-git-hooks.sh
generated: { by: "codex", at: "2026-10-09T15:26:03.952Z" }
verified:
  - by: openwiki/0.6.0
    at: 2026-10-09T15:26:03.952Z
---

# 快速開始與開發導覽

這個 repository 包含 Python 3.14 的 YouTube 轉錄/摘要平台、`apps/showcase` 的獨立 Nuxt 3 成果展示站，以及 `apps/browser-extension` 的 Chrome/Edge Manifest V3 client。Python 側提供 FastAPI、Streamlit、queue worker 和 RSS monitor；Extension 呼叫 FastAPI；Nuxt server routes 直接讀取 Notion。

## 最短本機啟動路徑

在 repository root：

```bash
cp apps/whisper_summary/.env.example apps/whisper_summary/.env
uv sync --project apps/whisper_summary --frozen --no-install-project
make api
```

另開 terminal 啟動 Streamlit：

```bash
make streamlit
```

API 預設為 `http://localhost:8080`，Streamlit 預設為 `http://localhost:8501`。預設自動摘要池包含 Gemini 與本機 Codex CLI；`apps/whisper_summary/.env` 請提供 `GOOGLE_GEMINI_API_KEY`，或確認 `CODEX_BIN` 指向可用的 Codex CLI。只有 OpenAI 或 Ollama key 仍無法使用目前的預設候選池；實際 pipeline 會寫入 Notion，因此正常處理也需要 `NOTION_API_KEY` 與 `NOTION_DATABASE_ID`。不要提交 `apps/whisper_summary/.env`。

建立 task 後 API 會把工作寫入 SQLite queue。設定 `PROCESSING_WORKER_TOKEN`（或沿用 `PROCESSING_LOCK_ADMIN_TOKEN`），另開 terminal 啟動常駐 processing worker；worker 透過 `TASK_API_BASE_URL` 呼叫 API：

```bash
make processing-worker
```

需要一次同步處理目前 queue 時，可在 API 仍執行的狀態下執行：

```bash
make run
```

本機下載另需 PATH 上的 `yt-dlp`；`uv sync` 不會安裝此執行檔。可用 `make yt-dlp-update` 安裝至 `/usr/local/bin/yt-dlp`，該位置可能需要寫入權限。

## Docker 啟動

```bash
docker compose up -d
```

這會啟動 API、Streamlit、processing worker 與 RSS monitor，對外提供 API `:8080` 與 Streamlit `:8501`。Streamlit、RSS monitor 與 processing worker 都透過 Compose 內的 `http://api:8080` 存取 API。API 與 processing worker container 啟動時預設更新 yt-dlp；不希望啟動時存取下載來源可在 Compose 載入的 `apps/whisper_summary/.env` 設定 `YTDLP_AUTO_UPDATE=0`。RSS monitor 還需 `RSS_MONITOR_ENABLED=true` 才會實際 polling。

## Nuxt Showcase

```bash
cd apps/showcase
npm install
npm run check-env
npm run dev
```

開發站預設在 `http://localhost:3000`。上述直接執行 `npm run dev` 的流程請使用 frontend `.env` 或預先匯出的環境變數。`make showcase` 會載入 `apps/showcase/.env` 後啟動。`npm run check-env` 在獨立程序中讀取該檔案，其結果不會傳給後續程序。Showcase 另提供 `/insights` 每週回顧；內容由 `content/weekly-insights/` 文件建置，執行 `npm run insights:check` 可驗證資料，dev/test/build 前置流程會自動重建 registry。必要設定為 Notion token 與 database id；標準 `NOTION_*` 名稱優先於相容的 `NUXT_*` 名稱。Showcase 是唯讀介面，不會啟動 Python processing pipeline。跨裝置已讀同步的首次連結在 `/settings/sync` 輸入個人同步碼；有效 session 之後會自動恢復。

## Browser Extension

先啟動 FastAPI，再到 Chrome/Edge 擴充功能頁啟用開發者模式，選擇「載入未封裝項目」並指向：

```text
apps/browser-extension
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
make lint
```

也可依測試層級分開執行 `make test-unit` 與 `make test-integration`。Browser Extension 的靜態驗證使用 `make extension-check`。CI 分別驗證 Python、Nuxt Showcase 與 Browser Extension；完整指令與阻擋條件見[開發規則與測試策略](operations/development-and-testing.md)。

執行 Nuxt suite 與 production build：

```bash
npm --prefix apps/showcase run test
npm --prefix apps/showcase run build
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
| 維護 RSS channel automation | [YouTube RSS 自動化](workflows/rss-automation.md) |
| 修改 Notion schema 或 Python/Nuxt 整合 | [Notion 資料整合](integrations/notion-and-showcase.md) |
| 修改 Showcase UX、read state 或 SWR | [Nuxt Showcase 使用體驗與資料快取](frontend/showcase-experience.md) |
| 維護 Showcase 每週回顧內容 | `apps/showcase/content/weekly-insights/` 與 `npm run insights:check`；流程見 [設定與部署](operations/configuration-and-deployment.md) |
| 設定跨裝置已讀同步、session 或 Upstash | [Showcase 跨裝置已讀同步](frontend/read-state-sync.md) |
| 設定 Docker、env、cache 或部署 | [設定、執行與部署](operations/configuration-and-deployment.md) |
| 新增或定位測試 | [開發規則與測試策略](operations/development-and-testing.md) |

## 常見檢查

- Showcase 無法載入：本機先執行 `npm run check-env`；部署後檢查平台環境設定與 server log。check-env 不驗證已部署 runtimeConfig 或 Notion 權限。
- 設定存在但仍無資料：檢查 Notion integration 權限、database id 與 status schema。公開 diagnostics／health API 已移除，錯誤細節不再提供給訪客；安全 log 分類見[設定、執行與部署](operations/configuration-and-deployment.md)。
- task 已 Pending 但未開始：確認 dedicated processing worker 正在執行，或用 `make processing-worker` 啟動；`POST /processing-jobs` 只會確認目前採 dedicated mode，`make run` 則會同步處理一次 queue。再以維運端點檢查 active task leases。
- Extension 無法送出：確認 Options API Base URL、API connectivity 與頁面是否為支援的 YouTube URL；channel handle 還需要 DOM 提供 channel id。
- RSS 沒有建立舊影片 tasks：首次 poll 只 seed watermark，這是避免回填整個歷史 feed 的預期行為。
