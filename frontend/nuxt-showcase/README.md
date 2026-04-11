# Nuxt Showcase

這是一個部署到 Vercel 的 Nuxt 3 展示頁，會直接從 Notion database 讀取最近 100 筆 `Completed` 結果並顯示在首頁。

## Commands

```bash
npm install
npm run dev
npm run test
npm run build
```

## Environment Variables

- `NOTION_API_KEY` 或 `NUXT_NOTION_API_KEY`
- `NOTION_DATABASE_ID` 或 `NUXT_NOTION_DATABASE_ID`
- `NOTION_STATUS_PROPERTY` 或 `NUXT_NOTION_STATUS_PROPERTY`（選填，若你的狀態欄位不是 `Status`）
- `NOTION_COMPLETED_STATUS` 或 `NUXT_NOTION_COMPLETED_STATUS`（選填，預設 `Completed`）
- `SHOWCASE_CACHE_TTL_SECONDS` 或 `NUXT_SHOWCASE_CACHE_TTL_SECONDS`（選填，預設 `3600`）

## Cache

`SHOWCASE_CACHE_TTL_SECONDS` 目前會同時控制列表與詳細 API 的 server / CDN cache。Server API route 會回傳：

```txt
Cache-Control: public, s-maxage=3600, stale-while-revalidate=3600
```

搭配 Vercel CDN 做簡易 SWR 快取；server process 內也保留最後成功的資料快照，當 Notion 暫時失敗時可優先回退。這個 TTL 不影響前端 local state，例如已讀標記仍由瀏覽器端自行管理。

## Diagnostics

若首頁顯示 `Missing Notion showcase configuration.`，可直接開：

```txt
/api/showcase/diagnostics
```

這個端點只會回傳「哪些設定有讀到」，不會洩漏實際 secret 值，適合用來檢查本機或 Vercel 的 env 是否真的進到 Nuxt server。

若 `diagnostics` 顯示正常，但首頁仍無法載入，可再開：

```txt
/api/showcase/health
```

這個端點會直接測試 Notion query，回傳成功筆數或精簡後的錯誤訊息，適合排查 integration 權限、database id、欄位名稱或 API 回應問題。
若 schema 內找不到 `Status`，系統會先嘗試自動偵測像是 `狀態` / `State` 等 `status` 或 `select` 欄位；仍不符時可用 `NOTION_STATUS_PROPERTY` 與 `NOTION_COMPLETED_STATUS` 明確指定。
