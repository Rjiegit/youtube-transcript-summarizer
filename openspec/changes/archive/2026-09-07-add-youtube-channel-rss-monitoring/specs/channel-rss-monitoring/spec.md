## ADDED Requirements

### Requirement: Periodic Channel RSS Polling
系統 SHALL 支援以可設定的輪詢間隔，定期讀取「已啟用」的 YouTube channel RSS feed URL，並解析 `published`、`updated`、`yt:videoId` 與影片 URL。系統預設輪詢間隔 SHALL 為每 1 小時（3600 秒），且 MUST 可透過設定覆寫。

#### Scenario: Poll configured feeds on interval
- **GIVEN** RSS 監控功能已啟用且存在兩筆啟用中的 channel 訂閱
- **WHEN** 到達下一個輪詢時間點
- **THEN** 系統 SHALL 依序嘗試抓取每個 feed 並解析最新項目

#### Scenario: Skip disabled channel subscription
- **GIVEN** 存在一筆 `enabled=false` 的 channel 訂閱
- **WHEN** monitor 執行輪詢
- **THEN** 系統 SHALL 不抓取該訂閱的 feed URL

#### Scenario: Use default 1-hour interval when no override
- **GIVEN** RSS 監控功能已啟用且未設定自訂輪詢間隔
- **WHEN** monitor 啟動並進入排程循環
- **THEN** 系統 SHALL 使用 3600 秒作為輪詢間隔

#### Scenario: Override interval by configuration
- **GIVEN** RSS 監控功能已啟用且設定自訂輪詢間隔為 900 秒
- **WHEN** monitor 啟動並進入排程循環
- **THEN** 系統 SHALL 使用 900 秒作為輪詢間隔

### Requirement: Deduplicate Discovered Videos
系統 SHALL 對 RSS 取得的影片做去重，採 `published` watermark 作為第一層過濾，並以 `video_id` 作為最終去重鍵，避免對同一影片重複建立任務。

#### Scenario: Skip duplicate video entries
- **GIVEN** 某影片 `video_id` 已在既有任務或去重狀態中存在
- **WHEN** 該影片再次出現在 RSS 輪詢結果
- **THEN** 系統 SHALL 跳過任務建立並記錄為 duplicate

#### Scenario: Filter old entries by published watermark
- **GIVEN** 某 channel 已記錄 `last_processed_published_at`
- **WHEN** 輪詢結果中的 entry `published` 小於或等於該 watermark
- **THEN** 系統 SHALL 不建立任務並標記為已處理範圍內

### Requirement: Auto Create Tasks For New Videos
系統 SHALL 對首次觀測到的新影片自動建立任務，並沿用既有自動處理觸發流程。

#### Scenario: Create task and trigger processing for a new video
- **GIVEN** 輪詢結果包含尚未處理過的新影片 URL
- **WHEN** RSS monitor 提交任務建立請求
- **THEN** 系統 SHALL 成功新增任務並觸發背景處理排程

### Requirement: Monitoring Status And Error Visibility
系統 SHALL 提供最近一次輪詢時間與成功/失敗資訊，並在失敗時保留錯誤原因。

#### Scenario: Record feed error without stopping whole monitor
- **GIVEN** 某個 feed 因網路錯誤無法讀取
- **WHEN** 監控執行該輪詢
- **THEN** 系統 SHALL 記錄該 feed 的錯誤資訊
- **AND** 系統 SHALL 繼續處理其他 feed
