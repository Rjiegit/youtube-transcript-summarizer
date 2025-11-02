# task-automation Specification

## Purpose
TBD - created by archiving change add-auto-processing-trigger. Update Purpose after archive.
## Requirements
### Requirement: Auto Schedule Processing After Task Creation
新增任務後系統 MUST 立即嘗試排程背景 worker，確保處理流程自動啟動且沿用 processing lock。

#### Scenario: API auto schedules worker on new task
- **GIVEN** `/tasks` 接收到有效的 YouTube URL
- **WHEN** 任務成功新增至指定資料庫
- **THEN** 系統 MUST 取得 processing lock 並排程背景 worker
- **AND** 回應體中 SHOULD 提供 worker 編號或提示訊息

#### Scenario: Lock prevents duplicate scheduling
- **GIVEN** `/tasks` 接收到有效請求
- **AND** 另一個 worker 已持有 processing lock
- **WHEN** 嘗試排程 worker
- **THEN** 系統 MUST 保留原有鎖並回傳告知處理已在進行中

### Requirement: Streamlit Submissions Use API Auto Scheduling
Streamlit 介面 MUST 透過 API 新增任務並反映自動排程結果。

#### Scenario: Streamlit surfaces successful auto scheduling
- **GIVEN** 使用者於 Streamlit 介面新增合法 URL
- **WHEN** API 回應任務建立成功並排程 worker
- **THEN** UI MUST 顯示成功新增與背景處理已啟動的提示

#### Scenario: Streamlit handles locking or API failure
- **GIVEN** Streamlit 介面新增任務
- **WHEN** API 回應鎖定中或無法連線
- **THEN** UI MUST 顯示對應提示（如處理已在進行或錯誤訊息）

