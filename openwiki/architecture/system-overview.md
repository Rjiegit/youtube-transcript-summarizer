---
type: architecture
title: 系統架構總覽
description: 說明任務 API、Streamlit、背景 worker、持久層與 Nuxt Showcase 之間的責任邊界及主要資料流。
tags: [architecture, pipeline, api, streamlit, nuxt]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-29T14:03:31.952Z
sources:
  - id: openwiki-source-e201e686a785f09b6d899f0b
    resource: repo://compose.yaml
  - id: openwiki-source-a5853bfe60c0ac906f6ab533
    resource: repo://frontend/nuxt-showcase/nuxt.config.ts
  - id: openwiki-source-59891cd71dd0c8a50b5690a9
    resource: repo://frontend/nuxt-showcase/server/utils/notion.ts
  - id: openwiki-source-822793b105256e659707b60b
    resource: repo://src/apps/api/main.py
  - id: openwiki-source-a7e947ed28796c0a02e849d0
    resource: repo://src/apps/ui/streamlit_app.py
  - id: openwiki-source-1725fcb51e0d75a6530a84d9
    resource: repo://src/apps/workers/cli.py
  - id: openwiki-source-7306be041ac80462bfae1fc5
    resource: repo://src/infrastructure/persistence/factory.py
  - id: openwiki-source-df04114da62d5e054970a89f
    resource: repo://src/services/pipeline/processing_runner.py
generated: { by: "codex", at: "2026-08-29T14:03:31.952Z" }
---

# 系統架構總覽

本 repository 由兩個相互關聯、但可獨立執行的應用組成。Python 主系統負責接受 YouTube 任務、執行媒體下載與 AI 摘要、保存任務及結果；`frontend/nuxt-showcase` 則是唯讀的 Nuxt 3 展示站，直接從 Notion 讀取已完成成果。兩者以 Notion 中的完成資料作為整合邊界，而不是彼此直接呼叫。

## 執行入口與責任

| 入口 | 責任 | 執行方式 |
| --- | --- | --- |
| FastAPI `src.apps.api.main:app` | 建立與重試任務、管理 RSS 訂閱、排程 worker、檢視或釋放全域 processing lock | `make api`，預設 port 8080 |
| Streamlit `src/apps/ui/streamlit_app.py` | 互動式建立、瀏覽與操作任務；把畫面和 session state 分派給 `ui_*` 模組 | `make streamlit`，預設 port 8501 |
| CLI `src.apps.workers.cli` | 選擇 SQLite 或 Notion backend，同步執行一次 queue drain，輸出處理統計 | `make run` 或 module invocation |
| RSS monitor `src.apps.workers.rss_monitor` | 輪詢已啟用的 YouTube channel feed，透過 API 建立新任務 | `make rss-monitor` |
| Nuxt Showcase | 以 server routes 查詢 Notion，提供成果列表與詳細頁 | `npm run dev`，預設 port 3000 |

Docker Compose 只編排 Python 側的 `api`、`streamlit` 與 `rss-monitor`。三者共用 repository volume 與 `.env`；Streamlit 和 RSS monitor 以 `http://api:8080` 連向 API。Nuxt showcase 不在此 Compose topology 中，通常獨立開發或部署。

## 主資料流

1. 使用者從 Streamlit、HTTP client 或 RSS monitor 送出 YouTube URL。
2. FastAPI 正規化 URL，透過 `DBFactory` 選擇 SQLite 或 Notion adapter，執行去重並建立待處理任務。
3. 新任務建立後，API 嘗試排程背景 worker。排程失敗不會撤銷已入列任務，response 會明確指出任務已排隊但 worker 未啟動。
4. `ProcessingWorker` 先取得 backend 的全域 processing lock，再逐一取得 task lock。它在同一 worker 內依序完成下載、轉錄、摘要、Markdown 保存、Notion 保存與 Discord 通知。
5. 每一筆任務的例外會轉成 `Failed` 狀態並累計失敗數；worker 繼續處理下一筆。queue 完成或取得任務失敗後，都會在 `finally` 釋放全域 lock。
6. 完成結果寫入 Notion 後，Nuxt server API 以自己的設定、schema mapping 與 SWR cache 讀取 `Completed` 結果；瀏覽器不會取得 Notion API key。

## 邊界與依賴方向

`src/domain/interfaces` 定義資料庫、轉錄、摘要與儲存抽象；application services 組合這些能力，`src/infrastructure` 提供 SQLite、Notion、媒體、LLM 與通知 adapter。`DBFactory` 是 queue backend 的集中選擇點：SQLite 為直接依賴，Notion client 則延遲 import，缺少 optional dependency 時轉為明確的 runtime error。

`ProcessingWorker` 透過 constructor factories 注入 downloader、transcriber、summarizer、summary storage、file manager、notifier 與 config。這使重型網路與模型依賴可在單元測試中替換，也界定新增 provider 或儲存 adapter 時的主要 extension seam。

Streamlit 是 FastAPI 的 client，而不是另一個 pipeline owner。CLI 則直接建立 backend 並呼叫同步的 `process_pending_tasks`。因此所有入口最終共享同一組 task persistence 與 processing-lock 語意，但觸發方式分為 HTTP background scheduling 與 command-line synchronous drain。

## 失敗與安全界線

- 不合法 URL 在建立任務前即被拒絕；Notion backend 缺少必要環境變數時回傳 client-visible configuration error。
- API 將未知 backend、optional Notion client 不可用和一般 persistence failure 分別映射為 422、503 或 500。
- processing lock 的讀取與釋放端點要求 `X-Maintainer-Token`；未設定、缺少及錯誤 token 分別有不同錯誤狀態。
- worker 的全域 lock 定期 refresh，以避免長時間轉錄被誤判為 stale；每筆 pipeline 失敗只影響該 task。
- Nuxt 的 secrets 留在 Nitro server runtime config，前端只取得公開的 build date 與 commit SHA。

## 延伸閱讀

- [任務生命週期與併發控制](../workflows/task-lifecycle.md)
- [媒體轉錄與摘要流程](../workflows/media-processing.md)
- [Notion 資料整合](../integrations/notion-and-showcase.md)
