## 1. Configuration and Monitoring Scaffold

- [ ] 1.1 在 `src/core/config.py` 新增 RSS 監控設定（enabled、feed URLs、poll interval、最小間隔保護）與預設值（預設 3600 秒）
- [ ] 1.2 新增 RSS monitor service 模組與啟動入口，支援週期性輪詢與可中止執行
- [ ] 1.3 在 README/開發文件補充 RSS 監控啟用方式與環境變數說明

## 2. Subscription Persistence and Repository

- [ ] 2.1 在 SQLite 新增 `rss_channel_subscriptions` 資料表與必要索引（含 `channel_id` unique）
- [ ] 2.2 實作 subscription repository（CRUD、enable/disable、讀取啟用中的訂閱）
- [ ] 2.3 將每 channel 的 `last_processed_published_at` 持久化並提供更新方法

## 3. Streamlit Channel Management UI

- [ ] 3.1 在 `src/apps/ui/streamlit_app.py` 新增 channel 管理區塊（列表、建立、編輯、刪除）
- [ ] 3.2 實作啟用/停用切換與輸入驗證（channel_id/feed URL）
- [ ] 3.3 提供操作結果回饋（成功/失敗訊息）並避免重複新增

## 4. Feed Parsing and Deduplication

- [ ] 4.1 加入 `feedparser`、`python-dateutil` 依賴，實作 YouTube RSS 抓取與解析流程（`published`/`updated`/`video_id`/URL）
- [ ] 4.2 實作 `published` watermark 過濾邏輯，並定義每個 channel 的 `last_processed_published_at` 更新策略
- [ ] 4.3 實作最終去重判斷（以 `video_id` 優先，URL 次之）並與既有任務資料來源比對
- [ ] 4.4 實作輪詢結果分類（new/duplicate/error）與結構化輸出

## 5. Task Creation and Processing Integration

- [ ] 5.1 將新影片導入既有任務建立流程，確保資料庫寫入與欄位完整
- [ ] 5.2 串接既有 auto scheduling 與 processing lock，驗證 RSS 來源任務行為一致
- [ ] 5.3 新增來源標記（RSS monitor）以供追蹤與後續分析

## 6. Observability and Reliability

- [ ] 6.1 記錄每輪輪詢狀態（開始/結束時間、成功/失敗、錯誤原因）
- [ ] 6.2 實作單一 feed 失敗不影響其他 feed 的容錯邏輯
- [ ] 6.3 新增最小必要告警或日誌訊息，便於排查輪詢異常

## 7. Tests

- [ ] 7.1 新增單元測試：subscription repository、輸入驗證與 UI action handler
- [ ] 7.2 新增單元測試：RSS 解析、去重策略、錯誤容錯
- [ ] 7.3 新增整合測試：UI 新增 channel 後可被 monitor 輪詢並建立任務
- [ ] 7.4 更新既有 `task-automation` 測試以涵蓋 RSS 來源 scenario
