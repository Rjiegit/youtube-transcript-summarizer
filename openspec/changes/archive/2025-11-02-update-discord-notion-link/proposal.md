## Why
- 現行 Discord 通知僅提供標題與 YouTube URL，需要另開 Notion 才能檢視摘要內容。
- 摘要已同步到 Notion，團隊希望通知直接附上該頁連結以加速檢閱。

## What Changes
- 擴充 Discord 通知格式，將 `NOTION_URL` 與任務 ID 組合成 Notion 頁面連結並附在訊息中。
- 更新設定與任務處理流程，傳遞 Notion 連結資訊給通知 helper。
- 調整單元測試與文件，說明新環境變數與通知內容。

## Impact
- 需要於部署環境新增並維護 `NOTION_URL`（例如 `https://www.notion.so/workspace-path`）。
- 通知訊息內容加長，需注意 Discord webhook 的排版與換行。
- 若任務缺少 Notion ID 或環境未設定，通知將退回原本格式並記錄資訊訊息。
