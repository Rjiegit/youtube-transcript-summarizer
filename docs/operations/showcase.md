# Showcase 設定與部署核對

所有設定皆供 Showcase server／build 使用；由 repository 根目錄執行 `npm --prefix apps/showcase run check-env` 檢查設定是否存在。此檢查不代表已驗證遠端權限。

## Notion 設定

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

## 分享網址與預覽核對

文章頁 `/results/{id}` 會在 SSR 等待資料後輸出文章標題、摘要、Open Graph / Twitter metadata 與 canonical URL，不需要 crawler 執行 JavaScript。所有文章共用 `public/share-preview.png`（1200 × 630 PNG）；圖片與 metadata URL 使用同一個公開網站 origin。

- `NUXT_PUBLIC_SITE_URL`：選填，預設 `https://video-knowledge.hellojie.me`。Preview deployment 若要讓分享預覽指向該版本，請設定成可公開存取的 preview HTTPS origin。
- 設定只使用 HTTPS origin，忽略 path、query 與 fragment；空白、無效 URL、HTTP URL 或包含帳密的 URL 會回退正式網站。
- 未設定 preview origin 時，canonical 與圖片仍指向正式網站；本機 SSR 測試會另外 GET 本機圖片，確認 build 內的實際資產。
- 上游讀取失敗且無成功快取時，SSR 回傳一般 5xx 錯誤並設定 `Cache-Control: no-store`。

`npm run test:ssr` 需先完成 `npm run build`，會啟動本機 production server，以延遲 Notion fixture 檢查原始 HTML、各 crawler UA、圖片 GET 與 502/no-store。測試使用假憑證，攔截外部請求，不需要 Notion 帳號；CI 在 build 後自動執行。

## 部署版本核對

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

## 排錯

公開的 `/api/showcase/diagnostics` 與 `/api/showcase/health` 已移除，首頁不再提供診斷連結。
列表與詳情 API 只回傳一般錯誤訊息，避免暴露內部設定或 Notion 原始錯誤。

本機可執行 `npm run check-env` 檢查環境變數是否存在；這不代表部署後的 runtimeConfig 正確，也不會驗證 Notion 權限。
部署後請從部署平台的 server log 排查：

- `[showcase] configuration unavailable`：必要設定缺少；log 只包含缺少的設定名稱或存在與否。
- `[showcase] Notion query failed`：Notion 讀取失敗；log 包含列表／詳情路由與預定義錯誤類型，不含原始回應或 secrets。快取背景更新失敗也會記錄。

請透過平台設定與 Notion integration 權限檢查問題，不要公開完整設定或原始 Notion 回應。
若 schema 內找不到 `Status`，系統會先嘗試自動偵測像是 `狀態` / `State` 等 `status` 或 `select` 欄位；
仍不符時可用 `NOTION_STATUS_PROPERTY` 與 `NOTION_COMPLETED_STATUS` 明確指定。

## 實作導覽

快取、搜尋與 SSR 行為見 [Showcase 使用體驗](../../openwiki/frontend/showcase-experience.md)；Notion 請求與失敗機制見 [Notion 整合](../../openwiki/integrations/notion-and-showcase.md)。
