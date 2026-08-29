---
type: workflow
title: 任務生命週期與併發控制
description: 說明任務建立、去重、背景排程、SQLite leases、狀態轉移、失敗重試與管理者 lock 操作。
tags: [tasks, queue, locking, concurrency, retry]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-29T14:03:31.952Z
sources:
  - id: openwiki-source-822793b105256e659707b60b
    resource: repo://src/apps/api/main.py
  - id: openwiki-source-84844fa4307e4c928a7cd3d3
    resource: repo://src/infrastructure/persistence/sqlite/client.py
  - id: openwiki-source-d95510dd9df5633e605ade1a
    resource: repo://src/services/tasks/processing_scheduler.py
  - id: openwiki-source-7722b0b050a91340f1fb6d2b
    resource: repo://src/services/tasks/task_creation.py
generated: { by: "codex", at: "2026-08-29T14:03:31.952Z" }
---

# 任務生命週期與併發控制

## 建立與去重

`POST /tasks` 先正規化並驗證 YouTube URL，再選擇 SQLite 或 Notion backend。`create_task_record` 查找相同 URL 最新且非失敗的 task：

- `Pending` / `Processing`：視為 active duplicate，API 回 409。
- `Completed` + `block_existing`：永久阻擋，RSS 使用此 policy。
- `Completed` + `cache_ttl`：建立時間仍小於 `TASK_CACHE_TTL_SECONDS` 時回 200 cached result，不排程 worker。
- 沒有上述情況：建立新的 `Pending` task，API 回 201。

建立完成後 API 嘗試取得 processing lock 並啟動 daemon thread。lock 已被其他 worker 持有時 task 仍保留 Pending，response 的 `processing_started=false` 提醒呼叫端稍後可用 `/processing-jobs` 再觸發。

## 兩層 SQLite lease

全域 `processing_lock` 限制同一 backend 同時只有一個 queue-draining worker。scheduler 會在啟動 thread 前先取得 lease；worker 使用同一 worker id 再確認 ownership，背景 refresher 定期更新 `locked_at`。另一 worker 只能在 lease 超過 timeout 後接管。release 也以 worker id 為條件，避免舊 worker清掉新 owner 的 lease。

per-task lease 則由 `acquire_next_task` 在 `BEGIN IMMEDIATE` transaction 中原子選出最舊 `Pending` task，或 lock 已 stale 的 `Processing` task，並同 transaction 寫入 `Processing`、worker id 與 locked time。這保護單筆 ownership，也允許 crash 後回收卡住的 task。

## 狀態轉移

```text
Pending -> Processing -> Completed
                     \-> Failed -> Failed Retry Created
                                  \-> 新 Pending retry task
```

成功時保存 title、summary、duration 與 Notion page id；失敗時保存 error 與 duration。任何離開 `Processing` 的 SQLite status update 都清除 task 的 locked_at/worker_id。worker 將單筆 exception 收斂為 `Failed` 後繼續下一筆，queue 空時停止並在 `finally` 釋放全域 lock。

Retry endpoint 只接受現況為 `Failed` 的 source task。它複製 URL/title 建立帶 `retry_of_task_id` 和 reason 的新 Pending task，再把 source 改為 `Failed Retry Created`，避免一般 dedup 查詢把舊失敗視為 active result。Retry endpoint 本身不自動排程 worker，呼叫端需另觸發 processing job。

## 管理者操作

`GET /processing-lock` 與 `DELETE /processing-lock` 都要求 `X-Maintainer-Token`。DELETE 支援 dry-run；一般 release 必須提供 matching `expected_worker_id`。force release 可設定最小 age threshold，未達門檻回 409。只有確認 worker 已死亡或 lease 無法自行回復時才應 force clear。

## Backend 差異

SQLite 提供 transaction-based task acquisition 和真實 global lease。Notion backend 只有 optimistic「取第一筆 Pending 後改 Processing」，global lock 為 no-op，所以只適合單 worker。application service 依賴 `BaseDB` contract，但不能假設所有 adapter 都有相同隔離保證。

## 延伸閱讀

- [系統架構總覽](../architecture/system-overview.md)
- [媒體轉錄與摘要流程](media-processing.md)
- [YouTube RSS 自動化](../integrations/rss-automation.md)
