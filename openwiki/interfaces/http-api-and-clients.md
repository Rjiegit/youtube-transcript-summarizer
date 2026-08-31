---
type: interface
title: HTTP API 與 Client 契約
description: 集中說明 Task API、RSS、worker scheduling 與 processing lock endpoints，以及 Streamlit、Extension、RSS monitor 的呼叫語意。
tags: [api, fastapi, contracts, clients, operations]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-31T13:51:03.458Z
sources:
  - id: openwiki-source-0030f56752f8cbf5e90a9d68
    resource: repo://frontend/nuxt-showcase/server/api/showcase/results.get.ts
  - id: openwiki-source-822793b105256e659707b60b
    resource: repo://src/apps/api/main.py
  - id: openwiki-source-0520e948964d45782d02b5a3
    resource: repo://src/apps/extension/service_worker.js
  - id: openwiki-source-5fa5731f7c4a5357f216d501
    resource: repo://src/apps/ui/ui_api.py
  - id: openwiki-source-0b294e3f86f4bc3838cb6ca2
    resource: repo://src/services/rss/channel_monitor.py
  - id: openwiki-source-25648eab61c0e46bdd2d19af
    resource: repo://src/services/rss/subscription_service.py
  - id: openwiki-source-d95510dd9df5633e605ade1a
    resource: repo://src/services/tasks/processing_scheduler.py
generated: { by: "codex", at: "2026-08-31T13:51:03.458Z" }
---

# HTTP API 與 Client 契約

FastAPI 是互動式入口與 background processing 之間的主要邊界。Streamlit、Browser Extension、RSS monitor 和一般 HTTP client 都使用它；Nuxt Showcase 不使用這組 API，而是由 Nitro server 直接查詢 Notion。

## Client 對應

| Client | 使用 endpoints | 特性 |
| --- | --- | --- |
| Streamlit | `/tasks`、`/tasks/{id}/retry`、`/processing-jobs`、`/processing-lock` | UI 將 status/body 交給 view layer，lock 操作可帶 maintainer token |
| Browser Extension | `/tasks`、`/rss/subscriptions` | 固定 SQLite；互動、timeout 與通知行為見 Extension 整合頁 |
| RSS monitor | `/tasks` | 固定 `source_type=rss`、SQLite 與 `block_existing` |
| 維運 client | `/processing-jobs`、`/processing-lock` | lock inspection/release 需要 maintainer token |

## 建立 Task

`POST /tasks` 接受 YouTube URL，另可指定 `db_type=sqlite|notion`、來源及 completed-task policy。API 先正規化/驗證 URL，再確認 Notion backend 必要設定並呼叫共用 task creation service。

主要 response semantics：

- `201 Created`：新 Pending task 已保存；API 隨後嘗試 schedule background worker。
- `200 OK`：相同 URL 的 Completed task 尚在 cache TTL 內，`cached=true`，不再 schedule。
- `409 Conflict`：已有 Pending/Processing task，或 `block_existing` 阻擋既有 Completed task。
- `400`：YouTube URL 或 Notion configuration 不合法/缺漏。
- `422`：不支援的 backend 等 request validation error。
- `503`：optional backend implementation 不可用。

新 task 已持久化後，scheduler 無法取得 processing lock 並不撤銷 task。Response 仍回 task id，但以 `processing_started=false` 表示目前沒有啟動 worker；client 可以稍後呼叫 `/processing-jobs`。反之，persistence failure 發生在 task 建立前，會回 500 且沒有成功入列契約。

## Retry 與 processing job

`POST /tasks/{task_id}/retry` 只接受 `Failed` source task。成功會建立新的 Pending task、保存 source relationship，並把舊 task 改成 `Failed Retry Created`。Endpoint 本身不 schedule worker，呼叫端需再觸發 `POST /processing-jobs`；不存在的 task 回 404，非 Failed 狀態回 409。

`POST /processing-jobs` 接受 backend 與可選 worker id。Scheduler 先取得 global processing lock，再啟動 daemon thread；成功回 `202 Accepted`。已有有效 lock 時回 409，thread 啟動失敗時釋放剛取得的 lease 並轉成 server error。這個 endpoint 只負責接受一輪 queue drain，不等待下載或摘要完成。

## RSS subscription

`POST /rss/subscriptions` 接受 channel id、可選 feed URL/title 及 enabled flag。輸入會驗證 channel id，service 再正規化 feed URL 並確認兩者一致。成功建立 SQLite subscription 回 201；duplicate 回 409。RSS subscription 無 Notion backend 選項，後續 polling 由獨立 monitor process 處理。

## Processing lock 管理

`GET /processing-lock` 與 `DELETE /processing-lock` 都要求 `X-Maintainer-Token` 等於 `PROCESSING_LOCK_ADMIN_TOKEN`：server 未設定 token 回 503、header 缺少回 401、值錯誤回 403。

GET 回目前 worker id、locked time、age 與是否超過 timeout。DELETE 支援：

- targeted release：`expected_worker_id` 必須符合目前 owner；
- force release：可另要求 lock age 至少達 `force_threshold_seconds`；
- dry run：只回 before/after snapshot，不修改 lock。

一般 task client 不應取得 maintainer token。Streamlit 只有在自己的 server process 可讀取 token 時才顯示管理能力；Browser Extension 完全不實作 lock endpoints。

## Backend 與安全邊界

API 允許選擇 SQLite 或 Notion task backend；HTTP schema 相同不代表相同的 persistence 與 concurrency 保證。這些差異只在[任務、鎖與結果持久化](../persistence/task-and-result-storage.md)維護，client 不應從 response shape 推論 multi-worker 安全性。

目前 task 建立與 RSS 建立端點本身沒有 application authentication。若 API 離開可信本機/內網，應由 reverse proxy、network policy 或後續 API auth 保護；`PROCESSING_LOCK_ADMIN_TOKEN` 只保護 lock 管理，不保護一般 task submission。

## 延伸閱讀

- [任務生命週期與併發控制](../workflows/task-lifecycle.md)
- [Browser Extension 任務與 RSS 入口](../integrations/browser-extension.md)
- [YouTube RSS 自動化](../integrations/rss-automation.md)
- [系統架構與端到端資料流](../architecture/system-overview.md)
