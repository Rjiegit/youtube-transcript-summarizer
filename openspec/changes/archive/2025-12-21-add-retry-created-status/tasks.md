## 1. Implementation
- [x] 1.1 更新 retry API，在建立新任務成功後將來源任務狀態改為 `Failed Retry Created`
- [x] 1.2 調整 Notion/SQLite adapter 允許寫入新狀態並確保查詢/顯示正常
- [x] 1.3 更新 UI 與 API 回應邏輯，讓狀態更新能在列表中反映
- [x] 1.4 補上單元測試，涵蓋 retry 成功後來源任務狀態變更與篩選行為
