## 1. Implementation
- [x] 1.1 建立 `src/apps/extension/` 結構與 Manifest V3 基本檔案
- [x] 1.2 實作 background/service worker：
  - action 按鈕送出目前 tab 的 YouTube URL
  - context menu 支援影片頁與連結項目
  - POST `/tasks`（預設 db_type=sqlite）
- [x] 1.3 實作 Options 頁（API Base URL 設定，使用 storage.sync）
- [x] 1.4 加入成功/失敗通知與錯誤訊息整理
- [x] 1.5 README 補充外掛安裝、設定與使用說明

## 2. Validation
- [ ] 2.1 手動驗證：影片頁 action 按鈕送出成功
- [ ] 2.2 手動驗證：右鍵選單（影片連結）送出成功
- [ ] 2.3 手動驗證：API Base URL 變更後可正確送出
- [ ] 2.4 手動驗證：錯誤時顯示失敗通知（無效 URL 或 API 連線失敗）
- [ ] 2.5 檢查 `flake8 .` 無新增 lint 問題（若有新增 Python 變更）
