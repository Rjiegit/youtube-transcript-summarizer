---
type: persistence
title: 任務、鎖與結果持久化
description: 比較 SQLite 與 Notion task backend，並說明 recent history、Markdown/JSON artifacts 與 Notion summary publication。
tags: [persistence, sqlite, notion, locking, artifacts]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-31T13:03:19.622Z
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
generated: { by: "codex", at: "2026-08-31T13:03:19.622Z" }
---

# 任務、鎖與結果持久化

系統有四種不同目的的持久化資料：task/queue state、RSS 與 recent-view state、本機摘要 artifacts，以及供分享與 Showcase 使用的 Notion pages。它們不是同一份資料的完全鏡像，失敗與一致性保證也不同。

## `BaseDB` 與 backend 選擇

`BaseDB` 定義 task新增、查詢、取得下一筆、狀態更新、URL去重、retry，以及 global processing lock lifecycle。`DBFactory` 依 `sqlite|notion` 建立 adapter；因此 application service能使用共用contract，但不能假設所有backend具有相同鎖語意。

| 能力 | SQLite | Notion |
| --- | --- | --- |
| Task CRUD/status | 本機 `tasks` table | Notion database properties |
| 取得下一筆 | `BEGIN IMMEDIATE` 原子 claim | 讀第一筆 Pending 後 best-effort 改 Processing |
| Task lease | `locked_at` + `worker_id`，可回收 stale task | 無真正 row lock |
| Global lock | 單列 lease、heartbeat、owner-aware release | methods 為 no-op |
| Multi-worker | 以 transaction/lease 協調 | 假設單一 worker |

相同API形狀只代表可替換性，不代表相同consistency guarantee。需要background concurrency時，SQLite是現行具實際鎖保證的backend。

## SQLite state

預設database path是 `data/tasks.db`。初始化會建立：

- `tasks`：URL、status、summary/error、duration、retry relationship、task lease、Notion page id與來源；
- `processing_lock`：固定 id=1 的global worker lease；
- `recent_task_history`：每個task最新的view timestamp；
- `rss_channel_subscriptions`：channel、feed、enabled、watermark與poll status/error。

Legacy database會在啟動時以 `ALTER TABLE` 補上已知缺少欄位。這是輕量的forward migration，沒有versioned rollback。

Task claim在 `BEGIN IMMEDIATE` transaction內選最舊Pending或stale Processing，並在同一transaction寫入Processing、worker id與locked time。Global lock允許同一owner續用，其他worker只能在timeout後接管；heartbeat與release都限制matching worker id。Task離開Processing時清除task lease。

Recent history不是task status：Streamlit打開結果時upsert view time，讀取按最新排序，並依TTL prune。刪除history不會刪除task或摘要成果。

## Notion task backend與summary publication

`NotionDB` 把database page當作task record，以URL、Name、Status等properties建立與更新。它可供CLI/API選為queue backend，但task acquisition與global lock沒有SQLite的原子性；並行worker可能取得同一task，因此文件與部署都必須維持單worker假設。

`SummaryStorage` 是另一個用途：pipeline不論task backend為何，都會建立承載摘要的Notion page，包含Title、URL、Model、預設false的Public與paragraph children。成功回傳的page id寫回task，供Streamlit、Discord link與後續查詢使用。Notion write失敗是pipeline failure，不會被本機Markdown成功掩蓋。

## 本機 artifacts

Summary output path預設是 `data/summaries/_summarized_<timestamp>_<video-id>_<sanitized-title>.md`。`FileManager`只清理basename、保留directory、建立缺少目錄並以UTF-8覆寫檔案；過長filename保留extension後截斷。

有下載metadata時，worker以實際Markdown path的stem建立 `.metadata.json` sidecar。JSON以UTF-8、`ensure_ascii=False`與indent寫入。因sidecar依已清理/截斷後的實際path命名，兩個artifact會保持配對。Sidecar寫入失敗只記warning並繼續Notion與task completion；Markdown或Notion寫入失敗則使task失敗。

下載媒體本身位於 `data/videos`，不是summary artifact。Repository guideline將 `data` 視為generated/large output，不應提交。

## 修改與遷移注意事項

- 新增task欄位時需同步domain `Task`、`BaseDB` contract、SQLite schema/migration、task adapter與Notion mapping。
- 改Notion property名稱時要同時檢查queue adapter、SummaryStorage、Nuxt schema detection與既有database。
- 改output filename時要維持Markdown/metadata sidecar pairing，並驗證長Unicode title。
- 新增backend不能只實作CRUD；必須明確定義task claim、global lock、stale recovery與retry semantics。

## 延伸閱讀

- [任務生命週期與併發控制](../workflows/task-lifecycle.md)
- [媒體轉錄與摘要流程](../workflows/media-processing.md)
- [Notion 資料整合與 Showcase 邊界](../integrations/notion-and-showcase.md)
- [模組邊界與外部依賴](../architecture/module-boundaries-and-dependencies.md)
