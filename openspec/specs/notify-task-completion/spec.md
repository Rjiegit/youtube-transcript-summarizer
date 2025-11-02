# notify-task-completion Specification

## Purpose
TBD - created by archiving change add-discord-task-notification. Update Purpose after archive.
## Requirements
### Requirement: Discord Notification On Task Completion
當任務轉錄與摘要流程成功完成並更新為 `Completed` 時，系統 MUST 透過 `DISCORD_WEBHOOK_URL` 指定的 Discord webhook 發送通知，內容需包含任務標題、原始 YouTube URL，以及在具備任務 ID 與環境變數 `NOTION_URL` 時組合出的 Notion 頁面連結（格式：`{NOTION_URL}/{task_id}`）。

#### Scenario: Completed task includes Notion link
- **GIVEN** 待處理任務擁有標題、原始 YouTube URL 與 Notion 任務 ID
- **AND** 環境變數 `DISCORD_WEBHOOK_URL` 與 `NOTION_URL` 均已設定
- **WHEN** 背景 worker 將任務狀態更新為 `Completed`
- **THEN** 系統 MUST POST 一則 Discord 訊息，訊息內 MUST 顯示任務標題、原始 YouTube URL 與 `{NOTION_URL}/{task_id}` 的 Notion 連結

### Requirement: Discord Notification Fallback
當 `DISCORD_WEBHOOK_URL` 未設定或通知請求失敗時，系統 MUST 繼續完成既有流程並記錄警告，不得中斷任務完成。此外，若缺少 Notion 連結所需資訊，通知 MUST 退回僅有標題與 YouTube URL 的格式並記錄資訊訊息。

#### Scenario: Missing webhook skips notification
- **GIVEN** 任務完成且 `DISCORD_WEBHOOK_URL` 未設定
- **WHEN** 系統準備發送通知
- **THEN** 系統 MUST 跳過通知流程並記錄缺少設定的資訊性訊息

#### Scenario: Webhook failure does not fail task
- **GIVEN** 任務完成且通知請求因網路或 Discord 回應錯誤而失敗
- **WHEN** 系統發送通知遇到錯誤
- **THEN** 系統 MUST 記錄警告並繼續以 `Completed` 狀態結束任務

#### Scenario: Missing Notion link inputs keeps original format
- **GIVEN** 任務完成且 `NOTION_URL` 未設定或任務缺少 Notion ID
- **WHEN** 系統發送 Discord 通知
- **THEN** 訊息 MUST 僅包含任務標題與原始 YouTube URL
- **AND** 系統 SHOULD 記錄訊息指出未附加 Notion 連結

