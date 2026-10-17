# Showcase 雲端影片收件匣

Showcase（既有 Vercel Nuxt server）→ Supabase durable pgmq queue → 本機 bridge → 既有 SQLite tasks → 原 processing-worker。
本機關機時網站仍能提交；沒有線上狀態列表、完成回報或結果同步。

## Supabase 安裝與權限

1. 建議建立專用 Supabase project，啟用 Data API，expose `public`；不要 expose `pgmq`、`pgmq_public`、`video_inbox_private`。
2. 以 postgres 套用 `supabase/migrations/202610170001_video_inbox.sql`。此為初始 migration，不可重複直接執行。若已手動套用舊 JWT 版本，請先在新測試 project 驗證，勿直接重跑或刪除含待領訊息的 queue。
3. Migration 只建立本收件匣的 queue、私有雜湊憑證表與三個受保護 RPC，不會撤銷其他 Queue 的 grants。若 anon／authenticated 能存取原始 pgmq schema／本 queue，或通用 pgmq_public API，會中止並整筆回滾。請使用新的私有 project，或由管理者評估原本授權，勿為了安裝而任意撤權。
4. 準備 Supabase publishable key。這不是收件授權；每個 RPC 還會驗證專用的 `x-video-inbox-key` header。submit token 僅可 submit，receiver token 僅可 read/delete；遺失、無效或未配置 token 一律拒絕。匿名／authenticated 即使知道 RPC 名稱，沒有正確 token 也無法執行工作。原始 queue 與憑證表不對 Data API 開放。
5. 在受控環境產生兩個**不同**的 256-bit 隨機 token，僅將 SHA-256 雜湊存入 `video_inbox_private.credentials`。不使用自簽 JWT、signing private key、service-role 或 secret key，因此沒有每日人工續期需求。

以下離線 Python 範例只建立新檔，權限為 0600；stdout 僅輸出雜湊 SQL，token 不出現在 SQL 或終端。請在 Git repository 以外的受控空目錄執行，將 SQL 輸出保存為 `credentials.sql`，再由 postgres／SQL Editor 執行。不要提交或分享 token 檔：

```python
import hashlib
import os
import secrets

for purpose in ('submit', 'receiver'):
    token = secrets.token_urlsafe(32)
    fd = os.open(purpose + '.token', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as output:
        output.write(token)
    digest = hashlib.sha256(token.encode()).hexdigest()
    print("INSERT INTO video_inbox_private.credentials (purpose, token_hash) "
          f"VALUES ('{purpose}', decode('{digest}', 'hex')) "
          "ON CONFLICT (purpose) DO UPDATE SET token_hash = EXCLUDED.token_hash;")
```

將 `submit.token` 內容配置到 Showcase **server-only** `VIDEO_INBOX_SUBMIT_TOKEN`，`receiver.token` 內容配置到本機 `VIDEO_INBOX_RECEIVER_TOKEN`。RPC 不接受 queue 名稱，SECURITY DEFINER 固定空 search_path；共用發送權限不代表讀取權限。固定 token 不會自然過期，需妥善保存並於洩漏、撤銷或維運輪替時更換。

### 輪替／撤銷

在新的空目錄為要輪替的用途產生新 token 與雜湊，執行該用途的 UPSERT，再更新對應 runtime 設定並重啟／依既有授權流程重新部署。雜湊更新後舊 token 立即失效，切換期間可能有短暫 403；訊息仍留在 queue，本機以退避重試，網站保留原 submission_id。若只需立即撤銷，以 postgres 刪除該用途 credentials row 即可；另一用途不受影響。不需要改動 Supabase project signing keys。

瀏覽器使用的是第三組個人提交碼 `VIDEO_INBOX_ACCESS_TOKEN`，只允許呼叫 Showcase API；不會拿到 submit／receiver token。沿用既有 constant-time 個人碼驗證，不新增帳號系統。

## Showcase 設定

在既有 Vercel project server environment 或本機 `apps/showcase/.env` 設定（不要加 `NUXT_PUBLIC_`）：

```dotenv
VIDEO_INBOX_ACCESS_TOKEN=<長隨機個人提交碼，安全提供給允許使用者>
VIDEO_INBOX_ORIGIN=https://你的網站網域
VIDEO_INBOX_SUPABASE_URL=https://你的專案.supabase.co
VIDEO_INBOX_PUBLISHABLE_KEY=<publishable key>
VIDEO_INBOX_SUBMIT_TOKEN=<submit.token 的內容，僅 server 使用>
```

設定後依既有流程重新 build／部署（需另外取得發布授權）。本機 origin 使用 `http://localhost:3000`；preview domain 需明確配置，沒有 wildcard。API 檢查 exact Origin + 提交碼，禁止跨來源 cookie 誤用。未設定時 fail closed；錯誤不洩漏 Supabase 原始回應。網站 `/submit` 輸入影片與提交碼；碼不寫 localStorage。網站公開頁面仍可瀏覽，但提交需要驗證。

瀏覽器送出前將 UUID 與網址存入 localStorage；回應遺失／重新整理／重試都沿用同一 UUID，直到確認成功。localStorage 不可用時不發送，避免失去冪等識別碼。若網址錯誤，按「清除待確認提交」再改網址；已送入雲端的工作仍可能處理。每次明確的新提交有新 ID；雲端重送可以產生多筆 queue 訊息，本機 receipt PRIMARY KEY 確保只接收一次。同 ID 換網址會隔離，不能覆蓋既有任務。

## 本機啟動

安裝既有依賴，設定 `apps/whisper_summary/.env`：

```dotenv
VIDEO_INBOX_SUPABASE_URL=https://你的專案.supabase.co
VIDEO_INBOX_PUBLISHABLE_KEY=<publishable key>
VIDEO_INBOX_RECEIVER_TOKEN=<receiver.token 的內容，僅本機使用>
VIDEO_INBOX_DB_PATH=data/tasks.db
VIDEO_INBOX_IDLE_SECONDS=300
VIDEO_INBOX_BATCH_LIMIT=20
TASK_CACHE_TTL_SECONDS=3600
```

在 repository 根目錄執行 `make video-inbox-bridge`。**DB_PATH 必須指向既有本機 API 的同一個 `data/tasks.db`**（容器需共用 volume）；bridge 不經 API，直接交易式入庫。SQLite 初始化自動新增 receipts／quarantine tables，不搬移既有資料。備份／還原務必包含整個 SQLite DB（含 receipts），避免只還原 tasks 破壞去重。

另外啟動既有 `make api` 與 `make processing-worker`，沿用原 worker token 與 TASK_API_BASE_URL。bridge 不啟動影片處理，不改 worker 的 60 秒輪詢／heartbeat。

啟動立即 read；每次領取 1 筆，visibility 預設 60 秒，只涵蓋短暫本機交易。單輪最多 20 筆，有工作立即接續（輪間 0.1 秒），空閒等 300 秒；錯誤從 5 秒倍增至 300 秒。HTTP timeout 15 秒、SQLite lock timeout 5 秒。若延遲超過 visibility，允許安全重送，交易與唯一鍵仍阻止重複建立；不需要長時間鎖住影片處理。

本機 BEGIN IMMEDIATE 將既有 URL 去重／快取政策、新 tasks 與 receipt 同交易提交；其他 SQLite create_task_record 呼叫也使用同一交易保護。入庫前當機：雲端重送。入庫後 delete 前當機／刪除失敗：receipt 命中，不再新增。不同 ID 同 URL 沿用 Pending/Processing 去重與 Completed TTL。一般成功只 delete，不 archive，沒有短 TTL。

無效 payload／同 ID 不同 URL 先寫本機 `video_inbox_quarantine`，成功後才 delete；隔離失敗則保留雲端訊息重試。隔離含原始 payload，僅供本機管理者檢查，請限制 DB 檔案存取及按需清理；一般 log 不含 URL、token 或原始錯誤。檢查範例：`SELECT message_id, received_at FROM video_inbox_quarantine;`。修正後以新 UUID 重新提交；不要隨意移除 receipts。

## 上線驗證清單

先在測試 project 套用 migration 及雜湊設定。使用 publishable key 與 `x-video-inbox-key` 呼叫 REST RPC，測試沒有 token／錯 token 均拒絕；submit token 僅能 submit、read/delete 拒絕；receiver token 僅能 read/delete、submit 拒絕。原始 queue 與 credentials 不應由 Data API 讀取。測試輪替後舊 token 失效且新 token 可用。

停止 bridge 後在 `/submit` 提交，確認訊息保留；啟動 bridge 確認本機 Pending 與 receipt 同時出現、雲端訊息刪除；中斷 delete 後重啟確認 task 數量不增加。最後用既有 worker 處理，確認 pipeline 正常。

### 排錯

- `credentials`／HTTP 401、403：檢查 publishable key、用途 token、資料庫雜湊設定及輪替後 runtime 是否已更新。
- `rate_limit`／429：上游限流，本機退避重試。
- `upstream`／其他 HTTP status：檢查 Supabase 專案狀態、RPC migration 與服務可用性。
- `network`：連線／timeout；檢查網路與 Supabase URL。
- `invalid_response`：上游未回傳有效 JSON。
- 本機 `local_database`：SQLite 存取／鎖／寫入問題；檢查 DB 路徑、磁碟與權限。`unexpected` 需由管理者進一步調查。

Showcase server 只記錄類別與 status，本機只記錄類別、status 與退避秒數；不記錄上游 body、URL、token 或原始 exception。對外仍統一顯示「尚未確認收件」，使用相同 ID 重試。

HTTP header 驗證透過 PostgREST 的 transaction-scoped `request.headers`，參考[官方 request settings 說明](https://postgrest.org/en/stable/references/transactions.html)。

官方依據：[Queue API](https://supabase.com/docs/guides/queues/api)、[pgmq](https://supabase.com/docs/guides/queues/pgmq)、[資料安全](https://supabase.com/docs/guides/database/secure-data)。read 隱藏至 visibility timeout，pop 會直接刪除，因此本實作不用 pop。
免費專案的低活動可能被暫停；每日數次有意義請求不是不暫停保證，不新增 keepalive。暫停期間提交失敗可保留 UUID 重試；恢復專案後重新啟動 bridge。參閱[官方暫停說明](https://supabase.com/docs/guides/platform/free-project-pausing)。

### 本機 SQL 回歸測試

在 repository root 執行 `bash supabase/tests/run-video-inbox.sh`。需 Docker；腳本建立自己的隔離 pgmq 1.10.0／Postgres 18 容器，結束時自動清理，不連接正式專案。

驗證：既有權限不變、migration 失敗回滾、正常安裝、缺少／錯用途 token、撤銷與替換、原始 queue／credentials 隔離、visibility 與 delete。

SQL 容器測試不涵蓋 Supabase hosted gateway 對 custom header 的傳遞或雲端專案部署設定；仍需按上述清單執行真實 E2E。沒有雲端憑證時不能宣稱已驗證這一段。

## 實作來源導覽

本頁維護安裝、權限、輪替與復原操作。Showcase 入口位於 `apps/showcase/server/api/video-inbox/`，本機 bridge 位於 `apps/whisper_summary/apps/workers/video_inbox_bridge.py`，資料庫定義位於 `supabase/migrations/202610170001_video_inbox.sql`。
OpenWiki 尚無獨立收件匣頁面；入庫後的處理機制見 [任務生命週期](../openwiki/workflows/task-lifecycle.md)。既有 Wiki 對 Showcase 唯讀的敘述僅適用文章讀取路徑，不涵蓋 `/submit`。
