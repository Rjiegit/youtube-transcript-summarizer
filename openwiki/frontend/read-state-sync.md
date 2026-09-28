---
type: frontend-guide
title: Showcase 跨裝置已讀同步
description: 說明 Nuxt Showcase 選用的 Upstash 已讀同步、session 驗證、時間戳合併與本機降級行為。
tags: [showcase, read-state, sync, upstash, authentication]
verified:
  - by: openwiki/0.4.3
    at: 2026-09-28T12:59:50.272Z
sources:
  - id: openwiki-source-6b1be9f1b66868fbfe965160
    resource: repo://apps/showcase/composables/useReadResults.ts
  - id: openwiki-source-b2141eed712a0d1e1148b8a1
    resource: repo://apps/showcase/server/api/read-state/mutations.post.ts
  - id: openwiki-source-9f5333e2cc4389f80938f0f7
    resource: repo://apps/showcase/server/api/read-sync/session.post.ts
  - id: openwiki-source-fb573f8eefb181df7d8bd35e
    resource: repo://apps/showcase/server/utils/read-sync-auth.ts
  - id: openwiki-source-3b0efe03f5b86982327fa144
    resource: repo://apps/showcase/server/utils/read-sync-config.ts
  - id: openwiki-source-0a3a0e5a5d4a4438ab28921a
    resource: repo://apps/showcase/server/utils/read-sync-server.ts
  - id: openwiki-source-ac66111399dbff368f8fbd32
    resource: repo://apps/showcase/server/utils/upstash-read-state.ts
generated: { by: "codex", at: "2026-09-28T12:59:50.272Z" }
---

# Showcase 跨裝置已讀同步

Showcase 預設把已讀狀態存在瀏覽器 `localStorage`。首頁的「跨裝置同步」開關讓使用者選用遠端同步；即使開啟，本機狀態仍供即時 UI 與遠端故障時使用。同步狀態、開關偏好與既有已讀資料分別保存在 localStorage。

## 設定與資料邊界

Nuxt server 只有在 `READ_STATE_SYNC_ENABLED` 為 true 類值，且 Upstash REST URL/token、個人同步碼、session secret 都存在時，才視為已配置。`READ_STATE_SYNC_SPACE_ID` 預設 `personal`，決定 Redis hash 的 namespace。這些值只放在 private runtime config；瀏覽器不會取得 Redis token。

Redis key 是 `showcase:read-state:{spaceId}`，field 為內容 key，value 包含 `read|unread` 與 ISO `updatedAt`。保留 `unread` 記錄作為 tombstone，使其他裝置較舊的 read 記錄不會復活。Upstash mutation 使用 Lua script 比較時間戳，僅較新的更新會寫入，並回傳完整 hash snapshot。

## Session 與 API

`POST /api/read-sync/session` 比對個人同步碼，成功後簽發 30 天 HMAC session cookie；cookie 為 HttpOnly、SameSite Lax，production 使用 Secure。`GET` 回報可用與驗證狀態，`DELETE` 清除 cookie。`GET /api/read-state` 與 `POST /api/read-state/mutations` 需要有效 session；未配置回 503，未驗證回 401。Mutation API 最多接受 1000 筆，驗證內容 key、狀態與時間戳；所有私人 API 回 `Cache-Control: private, no-store`。

Session token 綁定 sync space id、過期時間與 HMAC 簽章。換掉 session secret 會使舊 cookie 失效；換掉 space id 則會讀到另一個 hash。個人同步碼與 Redis token 不應加入 public runtime config。

## 合併與故障行為

首次連線先取得遠端 snapshot，將舊本機 read 記錄轉成同步格式，再以較新的 `updatedAt` 決定每篇文章的狀態；本機勝出的項目補傳到 server。使用者標記 read/unread 時先更新本機，再非同步送出 mutation。遠端失敗時 UI 保留本機資料並顯示錯誤；下次回到頁面會重試。關閉開關會停止遠端請求，不清除本機、Redis 或 session。

本機已讀 map 最多保留 500 筆，同步 map 最多保留 1000 筆；失敗或無法使用 localStorage 時，當前頁面仍可使用記憶體中的狀態。

## 驗證與延伸

`apps/showcase/tests/read-sync-auth.test.ts`、`read-sync-config.test.ts` 與 `upstash-read-state.test.ts` 分別檢查驗證、設定與 Redis 合併。前端經由 `/api/read-state` 存取同步資料，server 使用 `ReadStateRepository` 介面包住 Upstash，替換儲存層時可保留前端 API 契約。

相關閱讀：[Showcase 使用體驗](showcase-experience.md)、[設定與部署](../operations/configuration-and-deployment.md)。
