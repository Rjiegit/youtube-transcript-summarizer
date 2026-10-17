# Showcase 已讀同步安裝與維運


設定同步服務後，已連結的裝置會自動同步已讀狀態。未連結的瀏覽器維持本機 `localStorage` 狀態，不會因公開瀏覽網站而取得同步權限。新裝置第一次使用時，前往 `/settings/sync` 輸入個人同步碼；驗證後 server 會發出 30 天 HttpOnly session cookie，之後該裝置會自動同步。Upstash Redis 是裝置間共享的同步來源，`localStorage` 仍保留作為 optimistic UI、離線 fallback 與舊資料遷移來源。

### 1. 建立 Upstash Redis

1. 在 Upstash Console 建立並認領 Redis database，確認帳戶與資料庫狀態。
2. 選擇靠近 Vercel Function 的 region；單人使用不需要先開 Global replication。
3. 維持 `Eviction` 關閉；已讀資料的 TTL 由應用程式設定，不要在 Upstash Console 再設另一個 TTL。
4. 從 database 的 REST API 區域取得 URL 與 token。

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
- `READ_STATE_SYNC_ACCESS_TOKEN`：新裝置第一次連結時，在 `/settings/sync` 輸入的個人同步碼。
- `READ_STATE_SYNC_SESSION_SECRET`：簽署 30 天 HttpOnly cookie 的獨立 secret。
- `READ_STATE_SYNC_SPACE_ID`：已讀資料 namespace。更換 access token 或 session secret 時不要改它，否則會看起來像全新的資料空間。
- `READ_STATE_SYNC_TTL_SECONDS`：已讀狀態保留期限，單位秒；預設 `2592000`（30 天）。每筆狀態在最後一次更新 30 天後會被清除；伺服器每次讀取或更新時會順便清理過期項目。整個 Hash 連續 30 天沒有同步活動也會過期。每個同步空間最多保留 100 筆狀態，超出時優先移除最舊的項目。

設定後可執行：

```bash
npm --prefix apps/showcase run check-env
```

輸出只顯示各項是否存在，不會印出 secret。部署到 Vercel 時，請把相同項目設在 Project Environment Variables 後重新部署。

### 3. 同步行為

- 每次載入時，前端會檢查裝置 session；已有有效 session 的裝置自動拉取遠端狀態並同步本機較新的狀態。
- 沒有有效 session 的瀏覽器只使用本機狀態。同步碼只在獨立的 `/settings/sync` 頁面輸入，不在首頁顯示設定控制。
- 驗證成功後，該裝置會在 session 有效期間自動同步；session 到期後可再次輸入同步碼連結。
- Upstash 暫時失敗或超過額度：畫面繼續使用本機狀態，後續刷新已讀狀態或重新載入頁面時會再次嘗試。

### 安全與維運注意事項

- 不要把 `UPSTASH_REDIS_REST_TOKEN`、個人同步碼或 session secret commit 到 repository。
- 個人同步碼應使用隨機長字串，不要使用一般帳號密碼。
- 遠端不可用時需保留本機狀態作為 fallback。
- 資料庫重新啟用或還原後若 endpoint 改變，要同步更新 server environment。
- Upstash 的 `Eviction` 必須保持關閉，避免資料在應用程式設定的 30 天期限前被容量策略淘汰。

## 輪替與重新連結

更換個人同步碼或 session secret 後重新部署。更換 session secret 會讓既有 cookie 失效，裝置需再次輸入同步碼；只更換同步碼不會撤銷既有有效 session。要撤銷既有 session 時一併更換 session secret。
保留原 `READ_STATE_SYNC_SPACE_ID` 以繼續使用原資料；更換 namespace 不會搬移資料。

## 實作導覽

Session API、Redis 資料模型、合併與失敗處理見 [OpenWiki 已讀同步](../../openwiki/frontend/read-state-sync.md)。
