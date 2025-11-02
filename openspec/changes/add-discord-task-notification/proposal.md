## Why
- 任務完成後缺乏即時通知，無法得知處理是否成功。
- 需求希望透過 Discord Webhook 在任務狀態為 Completed 時推播標題與 YouTube URL。

## What Changes
- 新增 Discord 通知模組，透過 `DISCORD_WEBHOOK_URL` 環境變數存取 webhook。
- 在任務成功完成並更新為 Completed 後觸發通知，訊息包含任務標題與原始 YouTube URL。
- 加入基本錯誤處理與紀錄，確保通知失敗不影響既有處理流程。

## Impact
- 需於部署環境設定 Discord Webhook，並確保 Secrets 管理妥善。
- 任務完成時將額外進行一次 HTTP 請求，可能增加極小的延遲。
- 需更新測試與文件說明通知配置方式。
