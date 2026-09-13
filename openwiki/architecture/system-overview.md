---
type: architecture
title: 系統架構與端到端資料流
description: 說明任務輸入、專用 worker、持久層與獨立前端應用之間的責任和資料流。
tags: [architecture, pipeline, api, worker, nuxt]
verified:
  - by: openwiki/0.4.3
    at: 2026-09-13T10:51:33.281Z
sources:
  - id: openwiki-source-f987324e0612a557c62a85fb
    resource: repo://apps/showcase/server/api/showcase/results.get.ts
  - id: openwiki-source-7c8ae95541eb7e7de0873e3d
    resource: repo://apps/showcase/server/utils/notion.ts
  - id: openwiki-source-e201e686a785f09b6d899f0b
    resource: repo://compose.yaml
  - id: openwiki-source-a816aff2ae090142dc0071cf
    resource: repo://tests/unit/test_dedicated_processing_worker.py
  - id: openwiki-source-342c9b983ccf76e13ea1243b
    resource: repo://whisper_summary/apps/api/dependencies.py
  - id: openwiki-source-ed9cac06ac45a553488b9905
    resource: repo://whisper_summary/apps/api/main.py
  - id: openwiki-source-d1e2e939cdaa20a1825bddb5
    resource: repo://whisper_summary/apps/api/routers/tasks.py
  - id: openwiki-source-5899750ee6dd474e4a72a34b
    resource: repo://whisper_summary/apps/ui/streamlit_app.py
  - id: openwiki-source-f6e59996a2bf7f9d896e2cd5
    resource: repo://whisper_summary/apps/workers/cli.py
  - id: openwiki-source-4796880dadec1e10c195387c
    resource: repo://whisper_summary/apps/workers/processing_worker.py
  - id: openwiki-source-aaaf86d61afa929bb997ee28
    resource: repo://whisper_summary/services/pipeline/processing_runner.py
  - id: openwiki-source-e66f0503669326252cbeb176
    resource: repo://whisper_summary/services/rss/channel_monitor.py
generated: { by: "codex", at: "2026-09-13T10:51:33.281Z" }
---

# 系統架構與端到端資料流

本 repository 包含 Python modular monolith、Browser Extension 與 Nuxt Showcase。Python package `whisper_summary` 提供 FastAPI、Streamlit、同步 CLI、dedicated processing worker 與 RSS monitor；Extension 呼叫 FastAPI，Showcase 則由 Nitro server routes 直接讀取 Notion。

## Runtime

| 入口 | 責任 |
| --- | --- |
| `whisper_summary.apps.api.main:app` | 建立／重試 task、RSS 訂閱及 processing lock 維運 API |
| `whisper_summary/apps/ui/streamlit_app.py` | 操作者 UI，透過 HTTP API 建立任務並檢視狀態 |
| `whisper_summary.apps.workers.processing_worker` | 持續輪詢 persisted queue，執行重型 pipeline |
| `whisper_summary.apps.workers.cli` | 同步 drain 一次 queue |
| `whisper_summary.apps.workers.rss_monitor` | 輪詢 YouTube feeds，透過 Task API 建立任務 |
| `apps/browser-extension` | Manifest V3 FastAPI client |
| `apps/showcase` | 直接讀取 Notion 完成成果的 Nuxt/Nitro app |

Compose 編排 `api`、`streamlit`、`processing-worker` 與 `rss-monitor`。Streamlit 與 RSS monitor 以 `http://api:8080` 連線；processing worker 直接使用 persisted backend。Showcase 不在此 Compose topology。

## 端到端流程

1. Streamlit、Extension、HTTP client 或 RSS monitor 向 FastAPI 送出 YouTube URL。
2. API 正規化、去重並把 task 持久化；API process 不啟動重型 pipeline。
3. Dedicated worker 週期性建立 backend，呼叫 `process_pending_tasks`。單次 polling cycle 失敗會記錄後繼續下一輪。
4. `ProcessingWorker` 取得全域 lock，逐筆 atomic claim task，完成 yt-dlp、faster-whisper、LLM、Markdown/JSON、Notion 與 Discord 流程；單筆失敗標記 Failed，並繼續處理。
5. Nuxt Showcase 從 Notion 讀取 Completed 結果，不呼叫 Python Task API，也不把 Notion credential送到瀏覽器。

```mermaid
flowchart LR
  UI[Streamlit / Extension / RSS] --> API[FastAPI]
  API --> Queue[SQLite / Notion task backend]
  Queue --> Worker[Dedicated processing worker]
  Worker --> Media[yt-dlp → faster-whisper → LLM]
  Media --> Files[Markdown / JSON]
  Media --> Notion
  Media --> Discord
  Notion --> Showcase[Nuxt Showcase]
```

Domain contracts、services 與 adapters 的方向見[模組邊界與外部依賴](module-boundaries-and-dependencies.md)；queue 與 lock 行為見[任務生命週期](../workflows/task-lifecycle.md)。
