# Data Model: UI 列表顯示 Notion URL

## Entities

- **處理紀錄 (ProcessingRecord)**
  - Fields:
    - `id`: 任務/紀錄唯一識別
    - `title`: 影片標題或摘要標題
    - `status`: 處理狀態（queued/running/done/error 等）
    - `created_at`: 建立時間
    - `summary_path`: 本地摘要檔路徑（選填）
    - `notion_url`: Notion 頁面 URL（可空）
  - Rules:
    - `notion_url` 若存在需為有效 URL 格式（含 https、notion.so 域名或工作區域域名）
    - 若 `notion_url` 為空，UI 顯示固定提示而非空白
    - 列表呈現時保持排序/搜尋/分頁行為不受 `notion_url` 有無影響

## Relationships

- 單筆處理紀錄對應 0..1 個 Notion URL；無交叉表。
