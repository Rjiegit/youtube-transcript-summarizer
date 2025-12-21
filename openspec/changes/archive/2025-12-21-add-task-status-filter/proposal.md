# Change: 加入任務狀態篩選

## Why
目前「Tasks in Database」列表無法依狀態篩選，使用者很難快速定位 Failed 任務以重新執行。

## What Changes
- 在「Tasks in Database」提供可多選的狀態篩選器
- 狀態選項依目前資料動態產生，預設為全部狀態
- 篩選套用於列表與分頁計算（總數、頁數、顯示內容）

## Impact
- Affected specs: task-status-filter (new)
- Affected code: `src/apps/ui/streamlit_app.py`
