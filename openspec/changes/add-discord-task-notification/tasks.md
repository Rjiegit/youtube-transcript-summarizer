## 1. 通知設定
- [ ] 1.1 更新 `Config` 或相關設定，支援讀取 `DISCORD_WEBHOOK_URL`。
- [ ] 1.2 建立 Discord 通知 helper，封裝 webhook POST 邏輯與錯誤處理。

## 2. 任務流程整合
- [ ] 2.1 在任務完成流程中呼叫通知 helper，傳遞標題與 YouTube URL。
- [ ] 2.2 確保通知失敗時僅記錄警告，不會中斷任務完成流程。
- [ ] 2.3 新增或更新單元測試，涵蓋成功與 webhook 失敗情境（Mock HTTP）。

## 3. 文件與驗證
- [ ] 3.1 檔案（如 README 或 `.env.example`）新增 `DISCORD_WEBHOOK_URL` 說明。
- [ ] 3.2 執行 `flake8` 與 `python -m unittest`（或等效測試指令）。
- [ ] 3.3 `openspec validate add-discord-task-notification --strict`，若環境限制需記錄原因。
