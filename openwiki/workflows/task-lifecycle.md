---
type: workflow
title: 任務生命週期與併發控制
description: 說明任務建立、去重、背景排程、SQLite leases、狀態轉移、失敗重試與管理者 lock 操作。
tags: [tasks, queue, locking, concurrency, retry]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-31T13:29:02.704Z
sources:
  - id: openwiki-source-822793b105256e659707b60b
    resource: repo://src/apps/api/main.py
  - id: openwiki-source-84844fa4307e4c928a7cd3d3
    resource: repo://src/infrastructure/persistence/sqlite/client.py
  - id: openwiki-source-d95510dd9df5633e605ade1a
    resource: repo://src/services/tasks/processing_scheduler.py
  - id: openwiki-source-7722b0b050a91340f1fb6d2b
    resource: repo://src/services/tasks/task_creation.py
generated: { by: "codex", at: "2026-08-31T13:29:02.704Z" }
---

# 任務生命週期與併發控制

本頁聚焦task的狀態與控制流；完整HTTP status/auth contract見[HTTP API 與 Client 契約](../interfaces/http-api-and-clients.md)，backend schema與一致性比較見[任務、鎖與結果持久化](../persistence/task-and-result-storage.md)。

## 建立與去重

建立流程先正規化YouTube URL，再由 `create_task_record` 查找相同URL最新且非失敗的task：

- `Pending` / `Processing`：視為active duplicate；
- `Completed` + `block_existing`：永久阻擋，RSS 使用此 policy。
- `Completed` + `cache_ttl`：建立時間仍在TTL內時重用既有結果；
- 沒有上述情況：建立新的 `Pending` task。

只有新task需要排程worker；cached或duplicate不啟動新處理。HTTP status與response欄位由[HTTP API 與 Client 契約](../interfaces/http-api-and-clients.md)統一說明。

## 排程與兩層 ownership

Scheduler在啟動daemon thread前先取得全域processing ownership；已有worker時不重複啟動，thread啟動失敗則釋放剛取得的ownership。Worker使用同一id確認ownership，處理期間refresh，並在所有退出路徑釋放。

每筆task另有獨立ownership：worker取得最舊可處理task，stale Processing task可在timeout後回收。這兩層控制分別避免同一backend被多個queue drain同時處理，以及同一task被重複處理。SQLite的transaction、lease欄位、owner-aware release與Notion差異只在[任務、鎖與結果持久化](../persistence/task-and-result-storage.md)維護。

## 狀態轉移

```text
Pending -> Processing -> Completed
                     \-> Failed -> Failed Retry Created
                                  \-> 新 Pending retry task
```

成功時保存title、summary、duration與Notion page id；失敗時保存error與duration。Worker將單筆exception收斂為`Failed`後繼續下一筆，queue空時停止並在`finally`釋放全域ownership。

Retry只接受現況為`Failed`的source task。它建立有relationship的新Pending task，再把source改成`Failed Retry Created`，避免舊失敗紀錄參與一般active-result判斷。Retry不自動排程worker。管理端點、authorization與force-release contract見API頁；backend實作保證見持久化頁。

## 延伸閱讀

- [系統架構與端到端資料流](../architecture/system-overview.md)
- [HTTP API 與 Client 契約](../interfaces/http-api-and-clients.md)
- [任務、鎖與結果持久化](../persistence/task-and-result-storage.md)
- [媒體轉錄與摘要流程](media-processing.md)
- [YouTube RSS 自動化](../integrations/rss-automation.md)
