# Change: 標記已建立重試任務的失敗狀態

## Why
目前重試會建立新任務，原失敗任務仍維持 Failed，導致狀態篩選一直反覆出現同一批失敗項目。

## What Changes
- 當建立 retry 任務成功後，將原失敗任務狀態更新為 `Failed Retry Created`
- 狀態篩選仍以任務現有狀態動態產生，`Failed Retry Created` 會出現在選項中
- Retry 按鈕仍只對 `Failed` 顯示，避免已重試的項目重複操作

## Impact
- Affected specs: `openspec/specs/task-retry/spec.md`
- Affected code: `src/apps/api/main.py`, `src/domain/interfaces/database.py`, `src/infrastructure/persistence/*`, `src/apps/ui/streamlit_app.py`
