## ADDED Requirements

### Requirement: Streamlit Channel Subscription Management UI
系統 SHALL 在 Streamlit 提供 channel 訂閱管理介面，支援新增、編輯、刪除與啟用/停用追蹤項目。

#### Scenario: Create channel subscription in UI
- **GIVEN** 使用者開啟 channel 訂閱管理頁面
- **WHEN** 使用者輸入有效的 `channel_id` 或 feed URL 並送出
- **THEN** 系統 SHALL 建立新訂閱並顯示成功訊息

#### Scenario: Enable or disable subscription in UI
- **GIVEN** 已存在 channel 訂閱資料
- **WHEN** 使用者切換該訂閱為啟用或停用
- **THEN** 系統 SHALL 更新 `enabled` 狀態並反映於列表

#### Scenario: Delete subscription in UI
- **GIVEN** 已存在 channel 訂閱資料
- **WHEN** 使用者在 UI 執行刪除並確認
- **THEN** 系統 SHALL 移除該訂閱資料

### Requirement: Persist Channel Subscriptions In SQLite
系統 SHALL 以 SQLite 持久化 channel 訂閱資料，至少包含 `channel_id`、`feed_url`、`enabled`、`last_processed_published_at`、`created_at` 與 `updated_at` 欄位。

#### Scenario: Store subscription records with required fields
- **GIVEN** 使用者從 UI 新增一筆訂閱
- **WHEN** 寫入 SQLite
- **THEN** 系統 SHALL 寫入必要欄位並產生 `created_at` 與 `updated_at`

#### Scenario: Prevent duplicated subscription by channel
- **GIVEN** 同一個 `channel_id` 已存在於訂閱資料
- **WHEN** 使用者再次新增相同 `channel_id`
- **THEN** 系統 SHALL 拒絕重複建立並提示已存在

### Requirement: Validate YouTube Subscription Inputs
系統 SHALL 驗證 channel 訂閱輸入值，僅接受有效 YouTube channel 訂閱格式。

#### Scenario: Reject invalid subscription input
- **GIVEN** 使用者輸入非 YouTube 格式或無法解析的 feed URL
- **WHEN** 使用者送出新增或編輯
- **THEN** 系統 SHALL 顯示驗證錯誤並拒絕儲存
