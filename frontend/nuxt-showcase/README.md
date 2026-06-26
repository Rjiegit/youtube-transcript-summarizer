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

- 建議優先使用：
  - `NOTION_API_KEY`
  - `NOTION_DATABASE_ID`
  - `NOTION_STATUS_PROPERTY`（選填，若你的狀態欄位不是 `Status`）
  - `NOTION_COMPLETED_STATUS`（選填，預設 `Completed`）
  - `SHOWCASE_CACHE_TTL_SECONDS`（選填，預設 `3600`）
- 相容 fallback：
  - `NUXT_NOTION_API_KEY`
  - `NUXT_NOTION_DATABASE_ID`
  - `NUXT_NOTION_STATUS_PROPERTY`
  - `NUXT_NOTION_COMPLETED_STATUS`
  - `NUXT_SHOWCASE_CACHE_TTL_SECONDS`

解析優先順序固定為：

```txt
runtimeConfig > NOTION_*/SHOWCASE_* > NUXT_*
```

空字串會視為未設定；`SHOWCASE_CACHE_TTL_SECONDS` 若不是有效正數，會回退到 `3600`。

## Cache

`SHOWCASE_CACHE_TTL_SECONDS` 目前會同時控制列表與詳細 API 的 server / CDN cache。Server API route 會回傳：

```txt
Cache-Control: public, s-maxage=3600, stale-while-revalidate=3600
```

搭配 Vercel CDN 做簡易 SWR 快取；server process 內也保留最後成功的資料快照，當 Notion 暫時失敗時可優先回退。這個 TTL 不影響前端 local state，例如已讀標記仍由瀏覽器端自行管理。

## Version Footer

頁尾右側會顯示目前部署版本，格式為：

```txt
YYYY.MM.DD · shortSha
```

例如 `2026.06.26 · ede74aa`。日期方便快速確認建置時間，commit short SHA 可用來比對 Git commit 或 Vercel deployment 是否已更新到預期版本。同一天多次部署時，請以 commit short SHA 為準。

建置時會自動注入版本資訊：

- `SHOWCASE_BUILD_DATE` / `NUXT_SHOWCASE_BUILD_DATE`：選填；未提供時會用建置當下的 Asia/Taipei 日期。
- `VERCEL_GIT_COMMIT_SHA`：Vercel 部署時優先使用。
- `SHOWCASE_COMMIT_SHA` / `NUXT_SHOWCASE_COMMIT_SHA` / `GITHUB_SHA` / `COMMIT_SHA`：其他 CI 或本機 build 可使用的 fallback。

若沒有 commit SHA，頁尾會顯示 `local`，代表目前不是可精準對應部署 commit 的版本。

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
