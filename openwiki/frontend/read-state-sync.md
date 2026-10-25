---
type: frontend-guide
title: Showcase 跨裝置已讀同步
description: 說明 Nuxt Showcase 選用的 Upstash 已讀同步、session 驗證、時間戳合併與本機降級行為。
tags: [showcase, read-state, sync, upstash, authentication]
sources:
  - id: openwiki-source-c321ea3ddbfbe176217a0eee
    resource: repo://apps/showcase/composables/useAccountReadResults.ts
  - id: openwiki-source-6b1be9f1b66868fbfe965160
    resource: repo://apps/showcase/composables/useReadResults.ts
  - id: openwiki-source-36cce2c34e32cbad2ec20271
    resource: repo://apps/showcase/pages/settings/sync.vue
  - id: openwiki-source-b2141eed712a0d1e1148b8a1
    resource: repo://apps/showcase/server/api/read-state/mutations.post.ts
  - id: openwiki-source-9f5333e2cc4389f80938f0f7
    resource: repo://apps/showcase/server/api/read-sync/session.post.ts
  - id: openwiki-source-3b0efe03f5b86982327fa144
    resource: repo://apps/showcase/server/utils/read-sync-config.ts
  - id: openwiki-source-0a3a0e5a5d4a4438ab28921a
    resource: repo://apps/showcase/server/utils/read-sync-server.ts
  - id: openwiki-source-ac66111399dbff368f8fbd32
    resource: repo://apps/showcase/server/utils/upstash-read-state.ts
generated: { by: "codex", at: "2026-10-25T16:13:59.896Z" }
verified:
  - by: openwiki/0.6.0
    at: 2026-10-25T16:13:59.896Z
---

# Showcase 跨裝置已讀同步

安裝、環境變數、憑證輪替與裝置重新連結見 [操作手冊](../../docs/operations/showcase-read-sync.md)。本頁說明 session、資料模型與合併機制。

關閉帳號模式時，Showcase 預設把已讀狀態存在瀏覽器 `localStorage`。裝置連結入口位於 `/settings/sync`；使用者輸入個人同步碼後，已有有效 session 的裝置在載入頁面時會自動恢復遠端同步。本機狀態仍供即時 UI 與遠端故障時使用；本機已讀資料及同步資料分別保存在 localStorage，但不再保存同步開關偏好。

## 設定與資料邊界

舊個人碼模式的 Nuxt server 只有在 `READ_STATE_SYNC_ENABLED` 為 true 類值，且 Upstash REST URL/token、個人同步碼、session secret 都存在時，才視為已配置。`READ_STATE_SYNC_SPACE_ID` 預設 `personal`，決定 Redis hash 的 namespace；`READ_STATE_SYNC_TTL_SECONDS` 預設 30 天。這些值只放在 private runtime config；瀏覽器不會取得 Redis token。

Redis key 是 `showcase:read-state:{spaceId}`，field 為內容 key，value 包含 `read|unread`、ISO `updatedAt` 與到期時間。保留 `unread` 記錄作為 tombstone，使其他裝置較舊的 read 記錄不會復活。Upstash Lua script 清理過期項目、最多保留 100 筆狀態，再依時間戳接受較新的 mutation；整個 hash 在閒置滿 TTL 後也會到期。

## Session 與 API

舊個人碼模式的 `POST /api/read-sync/session` 比對個人同步碼，成功後簽發 30 天 HMAC session cookie；cookie 為 HttpOnly、SameSite Lax，production 使用 Secure。`GET` 回報可用與驗證狀態，`DELETE` 清除 cookie。`GET /api/read-state` 與 `POST /api/read-state/mutations` 需要有效 session；未配置回 503，未驗證回 401。Mutation API 最多接受 1000 筆，驗證內容 key、狀態與時間戳，忽略超過同步 TTL 的舊 mutation；所有私人 API 回 `Cache-Control: private, no-store`。

Session token 綁定 sync space id、過期時間與 HMAC 簽章。換掉 session secret 會使舊 cookie 失效；換掉 space id 則會讀到另一個 hash。個人同步碼與 Redis token 不應加入 public runtime config。

## 舊模式的合併與故障行為

首次連線先取得遠端 snapshot，將舊本機 read 記錄轉成同步格式，再以較新的 `updatedAt` 決定每篇文章的狀態；本機勝出的項目補傳到 server。使用者標記 read/unread 時先更新本機，再非同步送出 mutation。遠端失敗時 UI 保留本機資料並顯示錯誤；下次回到頁面會重試。Session 無效時改顯示需要驗證並停用遠端同步；在設定頁解除連結不清除本機資料或 Redis。

本機已讀 map 最多保留 500 筆，同步 map 最多保留 100 筆；失敗或無法使用 localStorage 時，當前頁面仍可使用記憶體中的狀態。

## 受邀帳號模式

`SHOWCASE_ACCOUNT_AUTH_ENABLED=true` 時，`useReadResults` 改用 `useAccountReadResults`。
帳號開關會自動啟用同步，Redis URL/token 齊備即可配置儲存；實際授權仍要求 Supabase 設定及受邀 user ID 清單。
read-state API 驗證 Bearer access token，使用 `account:<Supabase user ID>` 隔離 namespace；不使用舊 cookie、個人同步碼或共用 space。
舊 session POST 回 410，GET 不回報舊模式可用；設定頁改為登入帳號提示。

公開訪客不記錄已讀；帳號狀態僅在登入期間存於記憶體並由 server 讀寫，不讀取舊 localStorage，也不自動遷移舊資料。
讀取與 mutation 透過共用 request queue 序列化；切換或登出帳號時清空狀態，並以 user ID 與 generation 丟棄過期回應或排隊操作。
狀態在 server 成功回應後更新，失敗顯示 error，不提供離線已讀操作；可重新整理重試。
操作與遷移限制見[帳號模式手冊](../../docs/operations/showcase-account-auth.md)。

## 驗證與延伸

`apps/showcase/tests/read-sync-auth.test.ts`、`read-sync-config.test.ts` 與 `upstash-read-state.test.ts` 分別檢查驗證、設定與 Redis 合併。前端經由 `/api/read-state` 存取同步資料，server 使用 `ReadStateRepository` 介面包住 Upstash，替換儲存層時可保留前端 API 契約。

相關閱讀：[Showcase 使用體驗](showcase-experience.md)、[設定與部署](../operations/configuration-and-deployment.md)。

帳號模式另由 `account-read-results.test.ts`、`account-read-space.test.ts` 與 `account-access.test.ts` 檢查訪客、帳號隔離、排隊順序與 token 驗證。
