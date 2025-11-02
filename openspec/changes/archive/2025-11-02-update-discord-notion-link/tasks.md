## 1. 設定與資料流
- [x] 1.1 `Config` 讀取 `NOTION_URL` 並調整 `.env.example`／文件說明。
- [x] 1.2 任務完成流程將 Notion ID 與基底網址傳遞給 Discord 通知 helper。

## 2. 通知格式
- [x] 2.1 Discord notifier 支援組合 Notion 連結並處理缺少資訊時的退回格式。
- [x] 2.2 單元測試涵蓋 Notion 連結存在與缺失、webhook 失敗的行為。

## 3. 驗證
- [x] 3.1 更新相關文件／樣板環境變數，新增 `NOTION_URL`。
- [x] 3.2 執行 `python -m unittest -v`。
- [x] 3.3 `openspec validate update-discord-notion-link --strict`。
