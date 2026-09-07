## Why

目前任務建立流程以手動貼入單一 YouTube URL 為主，無法針對固定關注的 channel 自動追蹤新影片。為了降低人工操作成本並避免漏掉更新，需要提供可持續執行的 RSS 監控與自動入列機制。

## What Changes

- 新增 YouTube channel RSS 監控能力，支援設定多個 channel feed URL；輪詢間隔預設每小時執行一次，並可透過設定調整。
- 新增 Streamlit 管理介面，可新增/編輯/啟用停用/刪除要追蹤的 YouTube channel。
- 新增去重機制，採 `published` watermark 做快速過濾，並以 `video_id` 做最終 idempotent 去重，避免同一影片因重複輪詢而重複建立任務。
- 監控到新影片時，自動建立 task（使用既有任務建立流程）並觸發既有自動處理流程。
- 新增監控執行結果與錯誤記錄，便於觀測最近一次輪詢時間、成功/失敗狀態與原因。
- 在設定層新增 RSS 監控相關環境變數，並提供安全預設值（預設關閉）。

## Capabilities

### New Capabilities
- `channel-rss-monitoring`: 定期輪詢指定 YouTube channel RSS，發現新影片後自動建立任務並觸發處理。
- `channel-subscription-management`: 在 Streamlit 管理 YouTube channel 訂閱清單，供 RSS monitor 使用。

### Modified Capabilities
- `task-automation`: 擴充自動處理觸發來源，除了 API 手動建立任務外，也涵蓋 RSS 監控自動建立的任務。

## Impact

- Affected code:
  - `src/core/config.py`（新增 RSS 監控設定）
  - `src/services/pipeline/processing_runner.py`（沿用或封裝既有處理觸發）
  - `src/infrastructure/media/downloader.py`（維持既有下載流程，無破壞性修改）
  - 新增 RSS 監控服務與排程進入點（預計放在 `src/services/` 與對應 `infrastructure` adapter）
  - `src/apps/ui/streamlit_app.py`（新增 channel 管理介面）
  - `src/infrastructure/persistence/`（新增或擴充 channel 訂閱資料存取）
- Affected systems:
  - 檔案輸出與現有 SQLite/Notion 任務流程（沿用）
  - SQLite 新增 channel 訂閱資料表（供 UI 管理與 monitor 讀取）
  - 外部依賴增加 RSS feed HTTP 讀取
- Dependencies:
  - 新增 `feedparser`（解析 YouTube Atom/RSS）
  - 新增 `python-dateutil`（解析 `published`/`updated` 時間）
  - HTTP client 沿用專案既有 `requests`/HTTP layer
- Risks:
  - RSS 暫時不可用或網路波動導致漏抓/延遲
  - 去重策略若不完整，可能重複建立任務
