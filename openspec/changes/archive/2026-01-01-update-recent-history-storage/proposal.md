# Change: update recent history storage to SQLite

## Why
目前最近開啟任務紀錄存於 session + JSON 檔案，無法集中管理與持久化查詢。改用 SQLite 可提供一致、可追蹤的紀錄來源。

## What Changes
- 將最近開啟任務紀錄持久化改為 SQLite 資料表。
- 紀錄欄位精簡為 `task_id` 與 `viewed_at`。
- 維持最近開啟排序、去重與 30 天保留機制。

## Impact
- Affected specs: task-recent-history
- Affected code: src/apps/ui/ui_history.py, src/infrastructure/persistence/sqlite/client.py, src/domain/interfaces/database.py
