---
type: frontend-system
title: Nuxt Showcase 使用體驗與資料快取
description: 說明 Showcase 的 SSR 頁面、Notion server API、SWR 快取、已讀狀態與重新整理行為。
tags: [nuxt, showcase, swr, caching, ux]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-29T14:03:31.952Z
sources:
  - id: openwiki-source-a2ee3d44daa07a05306e975e
    resource: repo://frontend/nuxt-showcase/composables/useReadResults.ts
  - id: openwiki-source-733fe84338ea973667cce511
    resource: repo://frontend/nuxt-showcase/pages/index.vue
  - id: openwiki-source-42e33c0d6107dd607fab1d17
    resource: repo://frontend/nuxt-showcase/pages/results/%5Bid%5D.vue
  - id: openwiki-source-0030f56752f8cbf5e90a9d68
    resource: repo://frontend/nuxt-showcase/server/api/showcase/results.get.ts
  - id: openwiki-source-fd5007644f26258bb86db843
    resource: repo://frontend/nuxt-showcase/server/utils/swr-cache.ts
  - id: openwiki-source-6f3d5ab2255c7aff38623726
    resource: repo://frontend/nuxt-showcase/tests/swr-cache.test.ts
generated: { by: "codex", at: "2026-08-29T14:03:31.952Z" }
---

# Nuxt Showcase 使用體驗與資料快取

Nuxt Showcase 是成果的唯讀瀏覽介面。首頁由 server-side `useFetch` 取得列表，詳細頁同樣在 server 階段取得單筆內容；Notion credentials 與呼叫均留在 Nitro server routes，瀏覽器只接觸 `/api/showcase/*`。

## 列表與詳細頁

首頁先去重，再以標題做 client-side、不分大小寫的搜尋，並將未讀項目排在已讀項目前。列表可一次標記目前篩選集合為已讀。詳細頁成功取得資料後，會把 Notion page id 與穩定 read key 一併標記，並以 Markdown renderer 顯示 block content；有效 YouTube URL 另產生 privacy-enhanced embed。

首頁和詳細頁都處理 loading、error 與 hydration。詳細頁在沒有 loading、沒有 fetch error 且沒有 item 時產生 404。頁面 title、description 與 social metadata 會跟隨結果內容更新。

## Client-only 已讀狀態

已讀紀錄以 Nuxt `useState` 保留 session 記憶體狀態，並在 browser 可用時同步到 `localStorage`；SSR 階段不讀取 browser API。資料會驗證 shape、合併跨 navigation 狀態，並只保留最近 500 筆。storage quota 或 privacy mode 失敗不阻止本次 session 的 in-memory 行為。

首頁在 mounted、activated、focus、重新變為 visible、返回 list route，以及 BFCache `pageshow` 時重新同步已讀狀態。這些事件也會在 server response 已超過自己的 `cache_ttl_seconds` 時觸發資料刷新。

## Server SWR cache

列表 route 使用單一 cache，詳細 route 則依 Notion page id 各有 cache；TTL 改變時會重建相應 cache。一般 `get` 的語意如下：

- fresh snapshot：立即回傳，不呼叫 fetcher；
- stale snapshot：立即回傳舊值並在背景更新，同時共用既有的 in-flight refresh；
- 沒有 snapshot：等待第一次 fetch，失敗則向上拋出；
- 背景更新失敗且已有 snapshot：保留舊值。

首頁使用 `?refresh=1` 明確要求 `cache.refresh`，response 設為 `Cache-Control: no-store`。forced refresh 不共用既有背景 refresh，並以遞增 refresh id 確保較晚啟動的 refresh 才能覆寫 snapshot；因此較慢結束的舊 request 不會蓋掉較新的資料。route 最外層仍以 `peek()` 作 Notion 暫時失敗的 fallback；完全沒有 snapshot 時才回 502。

Browser 端 stale refresh 也會去重同時請求。若 forced refresh 失敗，現有列表保持可見，不以錯誤覆寫畫面。

## 維運端點

`/api/showcase/diagnostics` 只揭露設定是否存在與解析後狀態，不回傳 secret；`/api/showcase/health` 實際執行 Notion query，用於區分環境設定問題與 database/schema/permission 問題。

## 延伸閱讀

- [Notion 資料整合](../integrations/notion-and-showcase.md)
- [設定、執行與部署](../operations/configuration-and-deployment.md)
- [測試策略與擴充指南](../testing/test-strategy.md)
