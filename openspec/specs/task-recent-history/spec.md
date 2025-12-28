# task-recent-history Specification

## Purpose
TBD - created by archiving change add-task-recent-history. Update Purpose after archive.
## Requirements
### Requirement: UI Task Recent History
系統 SHALL 在 Streamlit UI 記錄使用者近期開啟過的任務。記錄項目 SHALL 包含任務可用的 Notion URL，並 SHALL 以最近開啟者優先排序且去重複。

#### Scenario: View task adds to recent history
- **WHEN** 使用者在任務列表點擊 View 開啟任務詳情
- **THEN** 該任務被記錄為最近開啟並位於最前面

#### Scenario: Recent history includes Notion URL when available
- **WHEN** 使用者開啟的任務具備可用的 Notion URL
- **THEN** 最近開啟任務記錄保存該 Notion URL 以供快速存取

#### Scenario: Notion link click records the task
- **WHEN** 使用者點選任務的 Notion 連結（包含另開新視窗）
- **THEN** 該任務會被記錄為最近開啟並更新為最新順序

### Requirement: UI Task Viewed Marker
系統 SHALL 在任務列表中標示本次 session 內已開啟過的任務，讓使用者辨識已閱讀項目。

#### Scenario: Viewed task shows a marker in list
- **WHEN** 使用者已開啟過某任務詳情頁
- **THEN** 任務列表中該任務顯示「已看過」的標示

### Requirement: UI Task Recent History Retention
系統 SHALL 保留最近開啟任務記錄最多 30 天，並在超過期限時清理。記錄 SHALL 在重新整理後仍可取回。

#### Scenario: Expired history entries are removed
- **WHEN** 最近開啟任務記錄內的項目超過 30 天
- **THEN** 記錄會排除該項目

#### Scenario: Re-open task moves it to the top without duplication
- **WHEN** 使用者再次開啟已存在於近期記錄的任務
- **THEN** 記錄僅保留一筆該任務並移至最前面

