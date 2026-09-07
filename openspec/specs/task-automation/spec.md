# task-automation Specification

## Purpose
定義各種任務建立來源如何自動排程背景 worker，並遵守 processing lock 的互斥規則，確保 API 與 RSS 建立的任務使用一致的啟動、追蹤與避免重複執行機制。
## Requirements
### Requirement: Auto Schedule Processing After Task Creation
新增任務後系統 MUST 立即嘗試排程背景 worker，確保處理流程自動啟動且沿用 processing lock。此要求適用於任何任務建立來源（包含 API 手動提交與 RSS 監控自動建立）。

#### Scenario: API auto schedules worker on new task
- **GIVEN** `/tasks` 接收到有效的 YouTube URL
- **WHEN** 任務成功新增至指定資料庫
- **THEN** 系統 MUST 取得 processing lock 並排程背景 worker
- **AND** 回應體中 SHOULD 提供 worker 編號或提示訊息

#### Scenario: RSS monitor auto schedules worker on new task
- **GIVEN** RSS 監控偵測到新的 YouTube 影片 URL
- **WHEN** 任務成功新增至指定資料庫
- **THEN** 系統 MUST 取得 processing lock 並排程背景 worker
- **AND** 系統 MUST 記錄任務建立來源為 RSS 監控

#### Scenario: Lock prevents duplicate scheduling
- **GIVEN** 任務建立請求有效
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
