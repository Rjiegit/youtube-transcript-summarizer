# Nuxt Showcase

這是一個部署到 Vercel 的 Nuxt 3 展示頁，會直接從 Notion database 讀取最近 50 筆 `Completed` 結果並顯示在首頁。

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

搭配 Vercel CDN 做簡易 SWR 快取；server process 內也保留最後成功的資料快照，當 Notion 暫時失敗時可優先回退。這個列表快取 TTL 不影響已讀狀態；Upstash 已讀同步資料另有獨立的閒置到期時間。

## 跨裝置已讀同步（選用）

已讀狀態預設仍採原本的 `localStorage` 模式；沒有設定 Upstash，或使用者沒有開啟首頁的「跨裝置同步」toggle 時，行為完全不變。啟用後，Upstash Redis 是裝置間共享的同步來源，`localStorage` 仍保留作為 optimistic UI、離線 fallback 與舊資料遷移來源。

### 1. 建立 Upstash Redis

1. 在 Upstash Console 建立並認領一個 Redis database。臨時建立但未認領的 database 可能在 72 小時後刪除。
2. 選擇靠近 Vercel Function 的 region；單人使用不需要先開 Global replication。
3. 維持 `Eviction` 關閉；已讀資料的 TTL 由應用程式設定，不要在 Upstash Console 再設另一個 TTL。
4. 從 database 的 REST API 區域取得 URL 與 token。

同步實作透過 Nuxt server 呼叫 Upstash REST API，Redis token 不會送到 browser。資料保存在一個 Redis Hash：

```txt
showcase:read-state:{READ_STATE_SYNC_SPACE_ID}
```

每個 field 是文章的 read key，value 同時保存 `read` / `unread` 與 `updatedAt`。`unread` 不會直接刪除，避免另一台裝置的舊已讀狀態重新出現。

### 2. 設定環境變數

```dotenv
READ_STATE_SYNC_ENABLED=true
UPSTASH_REDIS_REST_URL=https://YOUR-DATABASE.upstash.io
UPSTASH_REDIS_REST_TOKEN=YOUR_SERVER_SIDE_REDIS_TOKEN
READ_STATE_SYNC_ACCESS_TOKEN=YOUR_PERSONAL_DEVICE_CODE
READ_STATE_SYNC_SESSION_SECRET=YOUR_COOKIE_SIGNING_SECRET
READ_STATE_SYNC_SPACE_ID=personal
READ_STATE_SYNC_TTL_SECONDS=2592000
```

可用以下指令分別產生 access token 與 session secret；兩者請使用不同值：

```bash
openssl rand -hex 32
```

- `READ_STATE_SYNC_ENABLED`：server-side feature flag。只有 `true` / `1` / `yes` / `on` 會啟用。
- `UPSTASH_REDIS_REST_URL`：Upstash REST endpoint。
- `UPSTASH_REDIS_REST_TOKEN`：只允許放在 server environment，不要加到 `runtimeConfig.public`。
- `READ_STATE_SYNC_ACCESS_TOKEN`：新裝置第一次啟用同步時，在 UI 輸入的個人同步碼。
- `READ_STATE_SYNC_SESSION_SECRET`：簽署 30 天 HttpOnly cookie 的獨立 secret。
- `READ_STATE_SYNC_SPACE_ID`：已讀資料 namespace。更換 access token 或 session secret 時不要改它，否則會看起來像全新的資料空間。
- `READ_STATE_SYNC_TTL_SECONDS`：已讀狀態保留期限，單位秒；預設 `2592000`（30 天）。每筆狀態在最後一次更新 30 天後會被清除；伺服器每次讀取或更新時會順便清理過期項目。整個 Hash 連續 30 天沒有同步活動也會過期。每個同步空間最多保留 100 筆狀態，超出時優先移除最舊的項目。

設定後可執行：

```bash
npm run check-env
```

輸出只顯示各項是否存在，不會印出 secret。部署到 Vercel 時，請把相同項目設在 Project Environment Variables 後重新部署。

### 3. 過渡期切換行為

- Toggle 關閉：只讀寫既有的 `nuxt-showcase-read-results`，不呼叫同步 API。
- 第一次開啟：檢查 server 設定與 session；尚未驗證時顯示同步碼表單。
- 驗證成功：先拉取 Redis snapshot，再依 `updatedAt` 合併本機舊資料並補傳本機較新的狀態。
- Toggle 再次關閉：停止遠端讀寫，但不刪除 localStorage、Redis 或 HttpOnly session。
- Upstash 暫時失敗或超過額度：畫面繼續使用本機狀態並顯示同步失敗，之後切回頁面會再次嘗試。

相關私人 API 一律回傳 `Cache-Control: private, no-store`：

```txt
GET    /api/read-sync/session
POST   /api/read-sync/session
DELETE /api/read-sync/session
GET    /api/read-state
POST   /api/read-state/mutations
```

### 安全與維運注意事項

- 不要把 `UPSTASH_REDIS_REST_TOKEN`、個人同步碼或 session secret commit 到 repository。
- 個人同步碼應使用隨機長字串，不要使用一般帳號密碼。
- Free tier 沒有 uptime SLA；`localStorage` 是遠端不可用時的 fallback，不應移除。
- Free database 長時間沒有活動時可能被封存；重新啟用或還原後若 endpoint 改變，要同步更新 Vercel env。
- Upstash 的 `Eviction` 必須保持關閉，避免資料在應用程式設定的 30 天期限前被容量策略淘汰。

### 未來加入帳號

前端只依賴 `/api/read-state`，server 端則透過 `ReadStateRepository` 隔離 Upstash。未來加入帳號時，可以把目前的 `READ_STATE_SYNC_SPACE_ID` 認領給登入使用者，或把 repository 換成 Postgres，而不用修改首頁與已讀 UI。既有 Redis Hash 也能依同一個 sync space 匯入新儲存層。

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
