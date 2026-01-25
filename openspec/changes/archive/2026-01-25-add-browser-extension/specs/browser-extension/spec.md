## ADDED Requirements
### Requirement: Browser Extension Sends YouTube URLs
系統 SHALL 提供 Chrome/Edge (Manifest V3) 外掛，能將 YouTube 影片 URL 送至後端 `/tasks`。

#### Scenario: Action 按鈕送出目前影片頁
- **WHEN** 使用者在 YouTube 影片頁點擊外掛 action 按鈕
- **THEN** 外掛取得目前 tab 的 URL 並 POST `/tasks` (payload 含 `url` 與 `db_type=sqlite`)

#### Scenario: 右鍵選單送出列表中的影片連結
- **WHEN** 使用者在 YouTube 影片連結上點擊右鍵選擇「送出摘要任務」
- **THEN** 外掛使用連結 URL 並 POST `/tasks` (payload 含 `url` 與 `db_type=sqlite`)

### Requirement: Extension Options Configure API Base URL
系統 SHALL 提供 Options 頁讓使用者設定後端 API Base URL，並在送出任務時使用該設定。

#### Scenario: Options 頁更新並套用設定
- **WHEN** 使用者在 Options 頁輸入新的 API Base URL 並儲存
- **THEN** 之後的送出請求使用該 Base URL

### Requirement: Extension Shows Result Notifications
系統 SHALL 在任務送出成功或失敗時顯示通知。

#### Scenario: 成功送出顯示成功通知
- **WHEN** `/tasks` 回應 201 並回傳任務資訊
- **THEN** 外掛顯示成功通知（含任務狀態或提示訊息）

#### Scenario: 送出失敗顯示錯誤通知
- **WHEN** `/tasks` 回應非 201 或網路錯誤
- **THEN** 外掛顯示失敗通知與錯誤原因

### Requirement: Extension Rejects Invalid URLs
系統 SHALL 在 URL 非有效 YouTube 影片連結時拒絕送出並提示錯誤。

#### Scenario: 無效 URL 阻止送出
- **WHEN** 使用者在非 YouTube 影片頁或無效連結觸發送出
- **THEN** 外掛不送出請求並顯示錯誤通知
