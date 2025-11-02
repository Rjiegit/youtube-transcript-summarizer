## Why
- 手動呼叫 `/processing-jobs` 或按下 Streamlit "Trigger" 才會啟動處理流程，使用體驗不連貫。
- 需求希望在新增轉錄任務後自動排程處理，同時沿用既有 processing lock 防止重複執行。

## What Changes
- API `POST /tasks` 在新增任務後自動排程背景 worker，並於鎖衝突時返回提示。
- Streamlit 介面改為透過 API 建立任務並共用自動排程行為，含失敗時的回饋。
- 共享鎖定與排程邏輯，以確保同一時間只有一個 worker 執行。

## Impact
- 背景 worker 啟動頻率增加，但仍受鎖限制避免衝突。
- Streamlit 需依賴 API；若 API 不可用需顯示錯誤或退回本地處理（視需求）。
- 需更新測試與文件確保新行為可預期。
