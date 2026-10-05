---
type: architecture
title: 系統架構與端到端資料流
description: 說明任務輸入、專用 worker、持久層與獨立前端應用之間的責任和資料流。
tags: [architecture, pipeline, api, worker, nuxt]
verified:
  - by: openwiki/0.6.0
    at: 2026-10-05T13:47:15.340Z
sources:
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
  - id: openwiki-source-5d30f93453a5fc9227aa0b47
    resource: repo://apps/whisper_summary/services/pipeline/processing_runner.py
  - id: openwiki-source-daab87d344d0f6ce8a388ee8
    resource: repo://apps/whisper_summary/services/rss/channel_monitor.py
  - id: openwiki-source-cd0dc7918ef6cec31d2ebde9
    resource: repo://apps/whisper_summary/tests/unit/test_dedicated_processing_worker.py
  - id: openwiki-source-e201e686a785f09b6d899f0b
    resource: repo://compose.yaml
generated: { by: "codex", at: "2026-09-28T16:59:07.681Z" }
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

Compose 編排 `api`、`streamlit`、`processing-worker` 與 `rss-monitor`。Streamlit、RSS monitor 與 processing worker 都以 `http://api:8080` 連線；task 的 SQLite ownership 集中於 API。Showcase 不在此 Compose topology。

## 端到端流程

1. Streamlit、Extension、HTTP client 或 RSS monitor 向 FastAPI 送出 YouTube URL。
2. API 正規化、去重並把 task 持久化；API process 不啟動重型 pipeline。
3. Dedicated worker 持續透過受 token 保護的 HTTP queue API claim task；單次 polling cycle 失敗會記錄後繼續下一輪。
4. API 以 SQLite lease 控制 task ownership，worker 持續 heartbeat，並以設定或 task override 選擇 legacy／LangGraph engine。處理包含 yt-dlp、faster-whisper、LLM、Markdown/JSON、Notion 與 Discord；單筆失敗標記 Failed，失去 lease 時停止更新該 task。
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
