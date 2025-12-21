## MODIFIED Requirements
### Requirement: Retry Failed Task via API
系統 MUST 提供建立 retry 任務的 API，且僅允許來源任務狀態為 Failed。

#### Scenario: Create retry task from failed item
- **GIVEN** 任務狀態為 Failed 且有有效 task_id
- **WHEN** 呼叫 retry API
- **THEN** 系統 MUST 建立新的 Pending 任務並保留原任務
- **AND** 新任務 MUST 記錄來源任務關聯與 retry reason（若有提供）
- **AND** 系統 MUST 將來源任務狀態更新為 `Failed Retry Created`

#### Scenario: Reject retry for non-failed status
- **GIVEN** 任務狀態不是 Failed
- **WHEN** 呼叫 retry API
- **THEN** 系統 MUST 拒絕請求並回應可理解的錯誤訊息

### Requirement: Streamlit Retry Button For Failed Tasks
Streamlit 列表頁 MUST 只對 Failed 任務顯示 Retry 按鈕，點擊後建立 retry 任務並提示結果。

#### Scenario: Retry button visible only for failed tasks
- **GIVEN** 列表頁載入任務清單
- **WHEN** 任務狀態為 Failed
- **THEN** UI MUST 顯示 Retry 按鈕
- **AND** 非 Failed 任務 MUST 不顯示 Retry 按鈕

#### Scenario: Retry success feedback
- **GIVEN** 使用者點擊 Failed 任務的 Retry
- **WHEN** API 建立 retry 任務成功
- **THEN** UI MUST 顯示成功提示
- **AND** 原任務狀態 MUST 更新為 `Failed Retry Created`（重新整理後可見）
