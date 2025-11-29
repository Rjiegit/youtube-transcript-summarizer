# Contracts: Processing Records Listing (with Notion URL)

## Endpoint

- **GET /processing-jobs** (或現有提供列表的端點)
  - Purpose: 返回處理紀錄列表，包含可選的 `notion_url`
  - Authentication: 與現有端點一致（如無則保持公開同層級）

### Request

- Query params: 沿用既有排序/搜尋/分頁參數（不新增）

### Response (JSON)

```json
{
  "items": [
    {
      "id": "string",
      "title": "string",
      "status": "queued|running|done|error",
      "created_at": "ISO8601 timestamp",
      "summary_path": "string or null",
      "notion_url": "https://www.notion.so/..." 
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 42
  }
}
```

### Rules

- `notion_url` 可為 `null` 或缺失，UI 需顯示替代訊息；不可回傳空字串。
- 若 `notion_url` 非法（格式錯誤），應在後端標準化為 `null` 或有效 URL；避免將無效值傳至 UI。
- 現有排序/搜尋行為保持不變；新增欄位不應改變 API 的排序邏輯。
