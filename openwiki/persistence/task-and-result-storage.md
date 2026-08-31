---
type: persistence
title: 任務、鎖與結果持久化
description: 比較 SQLite 與 Notion task backend，並說明 recent history、Markdown/JSON artifacts 與 Notion summary publication。
tags: [persistence, sqlite, notion, locking, artifacts]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-31T13:51:03.458Z
sources:
  - id: openwiki-source-9fbc07b2ec408ab8469cae35
    resource: repo://src/domain/interfaces/database.py
  - id: openwiki-source-71c6fb5bae534b32dd19c0ab
    resource: repo://src/infrastructure/persistence/notion/client.py
  - id: openwiki-source-84844fa4307e4c928a7cd3d3
    resource: repo://src/infrastructure/persistence/sqlite/client.py
  - id: openwiki-source-c58845fdbb50864c91205283
    resource: repo://src/infrastructure/storage/file_storage.py
  - id: openwiki-source-5858a6e533d57781fe90f469
    resource: repo://src/infrastructure/storage/summary_storage.py
  - id: openwiki-source-d2d5349a26b1726584ff4cde
    resource: repo://src/services/outputs/path_builder.py
  - id: openwiki-source-df04114da62d5e054970a89f
    resource: repo://src/services/pipeline/processing_runner.py
generated: { by: "codex", at: "2026-08-31T13:51:03.458Z" }
---

# 任務、鎖與結果持久化

系統有四種不同目的的持久化資料：task/queue state、RSS 與 recent-view state、本機摘要 artifacts，以及供分享與 Showcase 使用的 Notion pages。它們不是同一份資料的完全鏡像，失敗與一致性保證也不同。

## `BaseDB` 與 backend 選擇

`BaseDB` 定義 task 新增、查詢、取得下一筆、狀態更新、URL 去重、retry，以及 global processing lock lifecycle。`DBFactory` 依 `sqlite|notion` 建立 adapter；因此 application service 能使用共用 contract，但不能假設所有 backend 具有相同鎖語意。

| 能力 | SQLite | Notion |
| --- | --- | --- |
| Task CRUD/status | 本機 `tasks` table | Notion database properties |
| 取得下一筆 | `BEGIN IMMEDIATE` 原子 claim | 讀第一筆 Pending 後 best-effort 改 Processing |
| Task lease | `locked_at` + `worker_id`，可回收 stale task | 無真正 row lock |
| Global lock | 單列 lease、heartbeat、owner-aware release | methods 為 no-op |
| Multi-worker | 以 transaction/lease 協調 | 假設單一 worker |

相同 API 形狀只代表可替換性，不代表相同 consistency guarantee。需要 background concurrency 時，SQLite 是現行具實際鎖保證的 backend。

## SQLite state

預設 database path 是 `data/tasks.db`。初始化會建立：

- `tasks`：URL、status、summary/error、duration、retry relationship、task lease、Notion page id 與來源；
- `processing_lock`：固定 id=1 的 global worker lease；
- `recent_task_history`：每個 task 最新的 view timestamp；
- `rss_channel_subscriptions`：channel、feed、enabled、watermark 與 poll status/error。

Legacy database 會在啟動時以 `ALTER TABLE` 補上已知缺少欄位。這是輕量的 forward migration，沒有 versioned rollback。

Task claim 在 `BEGIN IMMEDIATE` transaction 內選最舊 Pending 或 stale Processing，並在同一 transaction 寫入 Processing、worker id 與 locked time。Global lock 允許同一 owner 續用，其他 worker 只能在 timeout 後接管；heartbeat 與 release 都限制 matching worker id。Task 離開 Processing 時清除 task lease。

Recent history 不是 task status：Streamlit 打開結果時 upsert view time，讀取按最新排序，並依 TTL prune。刪除 history 不會刪除 task 或摘要成果。

## Notion task backend 與 summary publication

`NotionDB` 把 database page 當作 task record，以 URL、Name、Status 等 properties 建立與更新。它可供 CLI/API 選為 queue backend，但 task acquisition 與 global lock 沒有 SQLite 的原子性；並行 worker 可能取得同一 task，因此文件與部署都必須維持單 worker 假設。

`SummaryStorage` 是另一個用途：pipeline 不論 task backend 為何，都會建立承載摘要的 Notion page，包含 Title、URL、Model、預設 false 的 Public 與 paragraph children。成功回傳的 page id 寫回 task，供 Streamlit、Discord link 與後續查詢使用。Notion write 失敗是 pipeline failure，不會被本機 Markdown 成功掩蓋。

## 本機 artifacts

Summary output path 預設是 `data/summaries/_summarized_<timestamp>_<video-id>_<sanitized-title>.md`。`FileManager` 只清理 basename、保留 directory、建立缺少目錄並以 UTF-8 覆寫檔案；過長 filename 保留 extension 後截斷。

有下載 metadata 時，worker 以實際 Markdown path 的 stem 建立 `.metadata.json` sidecar。JSON 以 UTF-8、`ensure_ascii=False` 與 indent 寫入。因 sidecar 依已清理/截斷後的實際 path 命名，兩個 artifact 會保持配對。Sidecar 寫入失敗只記 warning 並繼續 Notion 與 task completion；Markdown 或 Notion 寫入失敗則使 task 失敗。

下載媒體本身位於 `data/videos`，不是 summary artifact。Repository guideline 將 `data` 視為 generated/large output，不應提交。

## 修改與遷移注意事項

- 新增 task 欄位時需同步 domain `Task`、`BaseDB` contract、SQLite schema/migration、task adapter 與 Notion mapping。
- 改 Notion property 名稱時要同時檢查 queue adapter、SummaryStorage、Nuxt schema detection 與既有 database。
- 改 output filename 時要維持 Markdown/metadata sidecar pairing，並驗證長 Unicode title。
- 新增 backend 不能只實作 CRUD；必須明確定義 task claim、global lock、stale recovery 與 retry semantics。

## 延伸閱讀

- [任務生命週期與併發控制](../workflows/task-lifecycle.md)
- [媒體轉錄與摘要流程](../workflows/media-processing.md)
- [Notion 資料整合與 Showcase 邊界](../integrations/notion-and-showcase.md)
- [模組邊界與外部依賴](../architecture/module-boundaries-and-dependencies.md)
