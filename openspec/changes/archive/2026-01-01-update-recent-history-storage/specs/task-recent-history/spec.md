## MODIFIED Requirements
### Requirement: UI Task Recent History
系統 SHALL 在 Streamlit UI 記錄使用者近期開啟過的任務，並以最近開啟者優先排序且去重複。紀錄 SHALL 僅保存 `task_id` 與 `viewed_at`，並持久化於 SQLite 資料庫。

#### Scenario: View task adds to recent history
- **WHEN** 使用者在任務列表點擊 View 開啟任務詳情
- **THEN** 該任務被記錄為最近開啟並位於最前面

#### Scenario: Notion link click records the task
- **WHEN** 使用者點選任務的 Notion 連結（包含另開新視窗）
- **THEN** 該任務會被記錄為最近開啟並更新為最新順序

### Requirement: UI Task Recent History Retention
系統 SHALL 保留最近開啟任務記錄最多 30 天，並在超過期限時清理。記錄 SHALL 由 SQLite 來源提供並可在重新整理後取回。

#### Scenario: Expired history entries are removed
- **WHEN** 最近開啟任務記錄內的項目超過 30 天
- **THEN** 記錄會排除該項目

#### Scenario: Re-open task moves it to the top without duplication
- **WHEN** 使用者再次開啟已存在於近期記錄的任務
- **THEN** 記錄僅保留一筆該任務並移至最前面
