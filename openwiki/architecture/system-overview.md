---
type: architecture
title: 系統架構與端到端資料流
description: 說明任務輸入、專用 worker、持久層與獨立前端應用之間的責任和資料流。
tags: [architecture, pipeline, api, worker, nuxt]
sources:
  - id: openwiki-source-edc748d2ffa8cac498e9a351
    resource: repo://apps/showcase/content/weekly-insights/series.json
  - id: openwiki-source-3d0ab990c23027fbcac5d169
    resource: repo://apps/showcase/pages/insights/index.vue
  - id: openwiki-source-17de8480042164f5a9040c86
    resource: repo://apps/showcase/scripts/weekly-insights-content.mjs
  - id: openwiki-source-8de160800c7fe6a0417a5cac
    resource: repo://apps/showcase/server/api/showcase/insights/%5Bstart%5D.get.ts
  - id: openwiki-source-313f86b8d67fcded8d860c7b
    resource: repo://apps/showcase/server/api/showcase/insights/index.get.ts
  - id: openwiki-source-f987324e0612a557c62a85fb
    resource: repo://apps/showcase/server/api/showcase/results.get.ts
  - id: openwiki-source-7c8ae95541eb7e7de0873e3d
    resource: repo://apps/showcase/server/utils/notion.ts
  - id: openwiki-source-1733e19cd888bc4a90558aa4
    resource: repo://apps/whisper_summary/apps/api/dependencies.py
  - id: openwiki-source-e6eed307c821ffad09957373
    resource: repo://apps/whisper_summary/apps/api/main.py
  - id: openwiki-source-8a8f27feb31a478f83017412
    resource: repo://apps/whisper_summary/apps/api/routers/processing.py
  - id: openwiki-source-2f9fce5f97d840294b957a0b
    resource: repo://apps/whisper_summary/apps/api/routers/tasks.py
  - id: openwiki-source-7332ded4af4c5b8186446177
    resource: repo://apps/whisper_summary/apps/ui/streamlit_app.py
  - id: openwiki-source-3510ac90ffbd030c0a1f2f0d
    resource: repo://apps/whisper_summary/apps/workers/cli.py
  - id: openwiki-source-fb3a71308a5a59482c2767f3
    resource: repo://apps/whisper_summary/apps/workers/processing_worker.py
  - id: openwiki-source-79006d740abb2f90a0561607
    resource: repo://apps/whisper_summary/services/pipeline/engines.py
  - id: openwiki-source-5d30f93453a5fc9227aa0b47
    resource: repo://apps/whisper_summary/services/pipeline/processing_runner.py
  - id: openwiki-source-daab87d344d0f6ce8a388ee8
    resource: repo://apps/whisper_summary/services/rss/channel_monitor.py
  - id: openwiki-source-cd0dc7918ef6cec31d2ebde9
    resource: repo://apps/whisper_summary/tests/unit/test_dedicated_processing_worker.py
  - id: openwiki-source-e201e686a785f09b6d899f0b
    resource: repo://compose.yaml
generated: { by: "codex", at: "2026-10-10T15:06:52.784Z" }
verified:
  - by: openwiki/0.6.0
    at: 2026-10-10T15:06:52.784Z
---

# 系統架構與端到端資料流

本 repository 的三個應用位於頂層 `apps/`：`apps/whisper_summary/` 是 Python modular monolith，另有 Browser Extension 與 Nuxt Showcase。Python package 的 import 名稱仍是 `whisper_summary`，提供 FastAPI、Streamlit、同步 CLI、dedicated processing worker 與 RSS monitor；Extension 呼叫 FastAPI，Showcase 則由 Nitro server routes 直接讀取 Notion。

## Runtime

| 入口 | 責任 |
| --- | --- |
| `whisper_summary.apps.api.main:app` | 建立／重試 task、RSS 訂閱及 processing lock 維運 API |
| `apps/whisper_summary/apps/ui/streamlit_app.py` | 操作者 UI，透過 HTTP API 建立任務並檢視狀態 |
| `whisper_summary.apps.workers.processing_worker` | 持續輪詢 persisted queue，執行重型 pipeline |
| `whisper_summary.apps.workers.cli` | 同步 drain 一次 queue |
| `whisper_summary.apps.workers.rss_monitor` | 輪詢 YouTube feeds，透過 Task API 建立任務 |
| `apps/browser-extension` | Manifest V3 FastAPI client |
| `apps/showcase` | 直接讀取 Notion 完成成果的 Nuxt/Nitro app |

Compose 編排 `api`、`streamlit`、`processing-worker` 與 `rss-monitor`。Streamlit、RSS monitor 與 processing worker 都以 `http://api:8080` 連線；task 的 SQLite ownership 集中於 API。Showcase 不在此 Compose topology。Showcase 另提供每週洞察頁面，內容由 repository 中整理過的週報文件建置為靜態 registry，再由 Nitro server routes 提供總覽與單週資料；它不即時查詢 Notion。

每週洞察系列可附上經核對的 `topicTracks`，記錄話題變化及其完整週觀察。loader 僅在週報都已發布時輸出這些軌跡，並驗證分類與觀察週、整理欄位後交由頁面呈現；話題觀察連回對應單週回顧，分類洞見也可連到相關話題。此內容是整理好的質性記錄，不由頁面即時分析來源。

## 端到端流程

1. Streamlit、Extension、HTTP client 或 RSS monitor 向 FastAPI 送出 YouTube URL。
2. API 正規化、去重並把 task 持久化；API process 不啟動重型 pipeline。
3. Dedicated worker 持續透過受 token 保護的 HTTP queue API claim task；單次 polling cycle 失敗會記錄後繼續下一輪。
4. API 以 SQLite lease 控制 task ownership，worker 持續 heartbeat，並優先採用 task override，其次使用設定的預設值，最後回退 legacy engine，亦可選擇 LangGraph engine。處理包含 yt-dlp、faster-whisper、LLM、Markdown/JSON、Notion 與 Discord；單筆失敗標記 Failed，失去 lease 時停止更新該 task。
5. Nuxt Showcase 從 Notion 讀取 Completed 結果，不呼叫 Python Task API，也不把 Notion credential送到瀏覽器。

```mermaid
flowchart LR
  UI[Streamlit / Extension / RSS] --> API[FastAPI]
  API --> Queue[SQLite / Notion task backend]
  Queue -->|lease API| Worker[Dedicated processing worker]
  Worker --> Media[yt-dlp → faster-whisper → LLM]
  Media --> Files[Markdown / JSON]
  Media --> Notion
  Media --> Discord
  Notion --> Showcase[Nuxt Showcase]
```

Domain contracts、services 與 adapters 的方向見[模組邊界與外部依賴](module-boundaries-and-dependencies.md)；queue 與 lock 行為見[任務生命週期](../workflows/task-lifecycle.md)。


## 文件責任與閱讀順序

此頁維護應用責任與跨系統資料流；日常修改依下列主題深入，避免在架構概覽重複維護細節。

| 問題 | 主要文件 |
| --- | --- |
| HTTP payload、認證與 client 相容性 | [HTTP API 與 Client 契約](../interfaces/http-api-and-clients.md) |
| 任務狀態、claim、heartbeat 與失敗重試 | [任務生命週期與併發控制](../workflows/task-lifecycle.md) |
| SQLite、Notion 與檔案的儲存機制 | [任務、鎖與結果持久化](../persistence/task-and-result-storage.md) |
| Streamlit 列表、詳細頁與操作歷史 | [Streamlit 任務操作與狀態導覽](../frontend/streamlit-console.md) |
| 週報整理、checkpoint 與內容建置 | [每週回顧整理與內容發布流程](../workflows/weekly-insights.md) |
| Showcase 瀏覽、搜尋與快取 | [Nuxt Showcase 使用體驗與資料快取](../frontend/showcase-experience.md) |

Notion 的共用 schema 與 Python／Nuxt 契約集中於[Notion 資料整合](../integrations/notion-and-showcase.md)；環境設定與排錯集中於[設定、執行與部署](../operations/configuration-and-deployment.md)。
