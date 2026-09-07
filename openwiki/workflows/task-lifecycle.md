---
type: workflow
title: 任務生命週期與併發控制
description: 說明任務建立、去重、背景排程、SQLite leases、狀態轉移、失敗重試與管理者 lock 操作。
tags: [tasks, queue, locking, concurrency, retry]
verified:
  - by: openwiki/0.4.3
    at: 2026-09-07T14:09:43.292Z
sources:
  - id: openwiki-source-822793b105256e659707b60b
    resource: repo://src/apps/api/main.py
  - id: openwiki-source-84844fa4307e4c928a7cd3d3
    resource: repo://src/infrastructure/persistence/sqlite/client.py
  - id: openwiki-source-d95510dd9df5633e605ade1a
    resource: repo://src/services/tasks/processing_scheduler.py
  - id: openwiki-source-7722b0b050a91340f1fb6d2b
    resource: repo://src/services/tasks/task_creation.py
generated: { by: "codex", at: "2026-09-07T14:09:43.292Z" }
---

# 任務生命週期與併發控制

<!-- openwiki: broken internal link [../interfaces/http-api-and-clients.md] file "../interfaces/http-api-and-clients.md" does not exist. Fix the href or restore the target, then delete this comment. -->
<!-- openwiki: broken internal link [../persistence/task-and-result-storage.md] file "../persistence/task-and-result-storage.md" does not exist. Fix the href or restore the target, then delete this comment. -->
本頁聚焦 task 的狀態與控制流；完整 HTTP status/auth contract 見[HTTP API 與 Client 契約](../interfaces/http-api-and-clients.md)，backend schema 與一致性比較見[任務、鎖與結果持久化](../persistence/task-and-result-storage.md)。

## 建立與去重

建立流程先正規化 YouTube URL，再由 `create_task_record` 查找相同 URL 最新且非失敗的 task：

- `Pending` / `Processing`：視為 active duplicate；
- `Completed` + `block_existing`：永久阻擋，RSS 使用此 policy。
- `Completed` + `cache_ttl`：建立時間仍在 TTL 內時重用既有結果；
- 沒有上述情況：建立新的 `Pending` task。

<!-- openwiki: broken internal link [../interfaces/http-api-and-clients.md] file "../interfaces/http-api-and-clients.md" does not exist. Fix the href or restore the target, then delete this comment. -->
只有新 task 需要排程 worker；cached 或 duplicate 不啟動新處理。HTTP status 與 response 欄位由[HTTP API 與 Client 契約](../interfaces/http-api-and-clients.md)統一說明。

## 排程與兩層 ownership

Scheduler 在啟動 daemon thread 前先取得全域 processing ownership；已有 worker 時不重複啟動，thread 啟動失敗則釋放剛取得的 ownership。Worker 使用同一 id 確認 ownership，處理期間 refresh，並在所有退出路徑釋放。

<!-- openwiki: broken internal link [../persistence/task-and-result-storage.md] file "../persistence/task-and-result-storage.md" does not exist. Fix the href or restore the target, then delete this comment. -->
每筆 task 另有獨立 ownership：worker 取得最舊可處理 task，stale Processing task 可在 timeout 後回收。這兩層控制分別避免同一 backend 被多個 queue drain 同時處理，以及同一 task 被重複處理。SQLite 的 transaction、lease 欄位、owner-aware release 與 Notion 差異只在[任務、鎖與結果持久化](../persistence/task-and-result-storage.md)維護。

## 狀態轉移

```mermaid
stateDiagram-v2
    [*] --> Pending
    Pending --> Processing
    Processing --> Completed
    Processing --> Failed
    Failed --> FailedRetryCreated: 更新原始 task
    Failed --> PendingRetryTask: 建立 retry task
    state "Failed Retry Created" as FailedRetryCreated
    state "新 Pending retry task" as PendingRetryTask
    PendingRetryTask --> Processing
```

成功時保存 title、summary、duration 與 Notion page id；失敗時保存 error 與 duration。Worker 將單筆 exception 收斂為 `Failed` 後繼續下一筆，queue 空時停止並在 `finally` 釋放全域 ownership。

Retry 只接受現況為 `Failed` 的 source task。它建立有 relationship 的新 Pending task，再把 source 改成 `Failed Retry Created`，避免舊失敗紀錄參與一般 active-result 判斷。Retry 不自動排程 worker。管理端點、authorization 與 force-release contract 見 API 頁；backend 實作保證見持久化頁。

## 延伸閱讀

- [系統架構與端到端資料流](../architecture/system-overview.md)
<!-- openwiki: broken internal link [../interfaces/http-api-and-clients.md] file "../interfaces/http-api-and-clients.md" does not exist. Fix the href or restore the target, then delete this comment. -->
- [HTTP API 與 Client 契約](../interfaces/http-api-and-clients.md)
<!-- openwiki: broken internal link [../persistence/task-and-result-storage.md] file "../persistence/task-and-result-storage.md" does not exist. Fix the href or restore the target, then delete this comment. -->
- [任務、鎖與結果持久化](../persistence/task-and-result-storage.md)
- [媒體轉錄與摘要流程](media-processing.md)
<!-- openwiki: broken internal link [../integrations/rss-automation.md] file "../integrations/rss-automation.md" does not exist. Fix the href or restore the target, then delete this comment. -->
- [YouTube RSS 自動化](../integrations/rss-automation.md)
