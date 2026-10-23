# Showcase 受邀帳號登入與功能切換

Showcase 的文章、搜尋與分享預覽維持公開。啟用帳號功能後，Supabase Auth 管理 Email＋密碼與 session；Showcase server 驗證 Supabase access token，再以 `SHOWCASE_ALLOWED_USER_IDS` 限制可使用功能的帳號。網站不保存密碼，也不建立本機帳號資料庫。

登入介面使用現有 Vue 元件與網站的淺色／青綠色樣式，透過 `@supabase/supabase-js` 呼叫登入、登出、密碼重設和變更密碼；不需要另一套 UI 套件。邀請由 Supabase Dashboard 管理，網站不提供公開註冊表單。

## Feature Toggle

只使用 `SHOWCASE_ACCOUNT_AUTH_ENABLED` 一個總開關，預設為 `false`。

| 狀態 | 行為 |
| --- | --- |
| `false` | 維持既有提交碼、localStorage 與個人同步碼模式，不顯示帳號登入。 |
| `true` | 一起啟用登入／登出、受邀帳號提交影片與個人已讀同步。公開文章仍免登入，公開訪客不讀寫已讀狀態；舊提交碼與同步碼不再授權。 |

開關在建置／部署時讀取，修改後重新部署。帳號模式會自動啟用已讀同步，不需要另設 `READ_STATE_SYNC_ENABLED`；這個既有設定只控制關閉帳號模式時的個人同步碼功能。啟用帳號模式後，缺少必要設定的功能會回報無法使用，不會退回舊權限方式。

## 雲端設定與啟用順序

1. 在 Supabase 建立或選定專案，啟用 Email＋密碼登入，關閉公開註冊，設定正式網站和本機 `/login` 為允許的轉址。由 Dashboard 邀請帳號，受邀者開啟邀請連結後在登入頁設定密碼。密碼重設與邀請信需寄信服務；正式環境應設定自訂 SMTP。
2. 將 `SHOWCASE_SUPABASE_URL`、`SHOWCASE_SUPABASE_PUBLISHABLE_KEY` 和逗號分隔的 `SHOWCASE_ALLOWED_USER_IDS` 設在 Showcase server environment。URL 與 publishable key 會提供給瀏覽器；user ID 清單只存在 server。
3. 確認影片 Queue 和本機 bridge 設定齊全，保留 server-only `VIDEO_INBOX_SUBMIT_TOKEN`、Origin 驗證及 Queue 設定；`VIDEO_INBOX_ACCESS_TOKEN` 只供回退至舊模式。同時設定 `UPSTASH_REDIS_REST_URL` 和 `UPSTASH_REDIS_REST_TOKEN`，帳號已讀模式不需要舊個人同步碼或 cookie 簽章密鑰。
4. 將 `SHOWCASE_ACCOUNT_AUTH_ENABLED=true` 後重新部署，一次啟用整套帳號功能。
5. 測試受邀帳號登入、未列入名單的帳號被拒，以及公開文章仍可讀。確認未登入／舊提交碼都無法投稿，受邀帳號可提交，且本機 bridge 正常收件。檢查訪客沒有已讀按鈕、登入帳號跨裝置同步、不同帳號不互相看到狀態、登出後畫面不保留前一帳號資料。

帳號已讀模式以 `account:<Supabase user ID>` 為新 namespace，**不會自動搬移**舊 `READ_STATE_SYNC_SPACE_ID` 共用狀態或瀏覽器 localStorage。若需保留舊資料，先決定由哪個帳號認領，再執行一次性遷移。此模式只在登入期間從 server 讀寫，不提供離線已讀操作；網路失敗時畫面顯示未同步，後續可重新整理重試。

## 本機驗證

`npm --prefix apps/showcase run check-env` 只顯示設定是否存在，不印出密鑰，也不連接雲端。可在沒有 Supabase 專案時保持總開關為 `false`，執行測試與 build；使用假 token 的本機測試不能取代真實邀請、密碼重設、跨裝置同步與雲端 Queue 端到端驗證。
