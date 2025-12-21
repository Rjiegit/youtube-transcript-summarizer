# task-status-filter Specification

## Purpose
TBD - created by archiving change add-task-status-filter. Update Purpose after archive.
## Requirements
### Requirement: UI Task List Status Filter
系統 SHALL 在「Tasks in Database」列表提供可多選的狀態篩選，選項 SHALL 依所選資料庫的現有任務狀態動態產生，且預設為全部狀態。篩選結果 SHALL 影響列表顯示與分頁計算。

#### Scenario: Default shows all tasks
- **WHEN** 使用者未調整狀態篩選（預設全選）
- **THEN** 列表顯示所有狀態的任務，分頁計算基於所有任務數量

#### Scenario: Filter limits list and pagination
- **WHEN** 使用者僅選取特定狀態（例如 Failed）
- **THEN** 列表僅顯示符合狀態的任務，分頁計算僅基於篩選後任務數量

