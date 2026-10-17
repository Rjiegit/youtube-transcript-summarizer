# Discord 摘要入口設定

若要讓 Discord 完成通知附上知識庫摘要連結，在執行摘要流程的
`apps/whisper_summary/.env` 設定 `SHOWCASE_BASE_URL=https://knowledge.example.com`，
並重新載入 worker 環境。通知會使用摘要的 Notion page ID 連往 `/results/{id}`；
完成通知只附加知識庫摘要入口，不再附加 Notion 網址。未設定知識庫網址或網址／摘要頁 ID 無效時，
通知僅顯示完成標題與影片網址。Compose 的 env_file 變更需重新建立 worker container。

## 變更與核對

設定 `SHOWCASE_BASE_URL` 後重啟 worker；Compose 請使用 `docker compose up -d --force-recreate processing-worker` 重新載入環境。
以一筆可成功處理的任務確認完成通知連到正確 Showcase 網域及摘要頁。停用時移除該環境變數並重啟 worker。

通知產生、URL 驗證及 fallback 機制見 [媒體處理與完成通知](../../openwiki/workflows/media-processing.md#完成通知與知識庫導向)。
