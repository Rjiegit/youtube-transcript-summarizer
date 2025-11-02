## ADDED Requirements
### Requirement: Discord Notification On Task Completion
當任務轉錄與摘要流程成功完成並更新為 `Completed` 時，系統 MUST 透過 `DISCORD_WEBHOOK_URL` 指定的 Discord webhook 發送通知，內容需包含任務標題與原始 YouTube URL。

#### Scenario: Completed task sends Discord notification
- **GIVEN** 待處理任務擁有標題與原始 YouTube URL
- **AND** 環境變數 `DISCORD_WEBHOOK_URL` 已設定
- **WHEN** 背景 worker 將任務狀態更新為 `Completed`
- **THEN** 系統 MUST POST 一則 Discord 訊息，訊息內 MUST 顯示任務標題與原始 YouTube URL

### Requirement: Discord Notification Fallback
當 `DISCORD_WEBHOOK_URL` 未設定或通知請求失敗時，系統 MUST 繼續完成既有流程並記錄警告，不得中斷任務完成。

#### Scenario: Missing webhook skips notification
- **GIVEN** 任務完成且 `DISCORD_WEBHOOK_URL` 未設定
- **WHEN** 系統準備發送通知
- **THEN** 系統 MUST 跳過通知流程並記錄缺少設定的資訊性訊息

#### Scenario: Webhook failure does not fail task
- **GIVEN** 任務完成且通知請求因網路或 Discord 回應錯誤而失敗
- **WHEN** 系統發送通知遇到錯誤
- **THEN** 系統 MUST 記錄警告並繼續以 `Completed` 狀態結束任務
