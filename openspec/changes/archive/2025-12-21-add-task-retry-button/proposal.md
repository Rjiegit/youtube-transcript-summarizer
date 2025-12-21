# Change: Add retry task button for failed items

## Why
處理失敗後需要快速重新排程；目前只能手動新增 URL，無法從既有失敗項目直接重試。

## What Changes
- 新增 API 能從 Failed 任務建立一筆新的 retry 任務（原任務保留）。
- Streamlit 列表頁對 Failed 任務提供 Retry 按鈕，觸發重試建立。
- 僅允許 Failed 狀態執行 retry，其他狀態會被拒絕或不顯示按鈕。

## Impact
- Affected specs: task-retry (new)
- Affected code: `src/apps/api/main.py`, `src/apps/ui/streamlit_app.py`, `src/domain/interfaces/database.py`, `src/infrastructure/persistence/*`
