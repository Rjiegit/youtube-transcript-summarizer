# Change: Add recent task history in Streamlit UI

## Why
使用者在一次建立或瀏覽多個任務時，容易漏掉想回頭查看的項目，需要能辨識已看過任務並保留近期瀏覽記錄。

## What Changes
- 在 Streamlit UI 記錄使用者「開啟（View）」過的任務記錄，包含 Notion URL（若可用）
- 在任務列表中標示使用者已看過的任務
- 近期瀏覽記錄以較長生命週期的方式保留（30 天 TTL）並可跨重新整理
- 點選 Notion 連結（含另開新視窗）也會更新任務記錄

## Impact
- Affected specs: task-recent-history (new)
- Affected code: src/apps/ui/streamlit_app.py, data/ui_recent_history.json
