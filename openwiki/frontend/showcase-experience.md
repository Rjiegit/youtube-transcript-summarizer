---
type: frontend-guide
title: Nuxt Showcase 使用體驗與資料快取
description: 說明 Showcase 的 SSR 頁面、Notion server API、SWR 快取、已讀狀態與重新整理行為。
tags: [nuxt, showcase, swr, caching, ux]
sources:
  - id: openwiki-source-369da753c512075845679e7e
    resource: repo://apps/showcase/components/HighlightedTitle.vue
  - id: openwiki-source-bb92958ed21ee9cf0accb45d
    resource: repo://apps/showcase/components/ReadSyncControl.vue
  - id: openwiki-source-6b1be9f1b66868fbfe965160
    resource: repo://apps/showcase/composables/useReadResults.ts
  - id: openwiki-source-8f9c3fc6564a596df49d04e9
    resource: repo://apps/showcase/pages/index.vue
  - id: openwiki-source-3d0ab990c23027fbcac5d169
    resource: repo://apps/showcase/pages/insights/index.vue
  - id: openwiki-source-714810166c8a4a2d54858dbf
    resource: repo://apps/showcase/pages/results/%5Bid%5D.vue
  - id: openwiki-source-36cce2c34e32cbad2ec20271
    resource: repo://apps/showcase/pages/settings/sync.vue
  - id: openwiki-source-6b47ec2bb946dbfe3f605cea
    resource: repo://apps/showcase/README.md
  - id: openwiki-source-f987324e0612a557c62a85fb
    resource: repo://apps/showcase/server/api/showcase/results.get.ts
  - id: openwiki-source-98886cf9c4725ca201459fa1
    resource: repo://apps/showcase/server/plugins/showcase-error-cache.ts
  - id: openwiki-source-51d27e8448c6ca65ff1ee504
    resource: repo://apps/showcase/server/utils/showcase-errors.ts
  - id: openwiki-source-acc677c60f44374b1f2d50cf
    resource: repo://apps/showcase/server/utils/swr-cache.ts
  - id: openwiki-source-c2ec24a0ccca33febfd50837
    resource: repo://apps/showcase/tests/swr-cache.test.ts
  - id: openwiki-source-218f09975f8887eb7efa96c4
    resource: repo://apps/showcase/tests/title-search.test.ts
  - id: openwiki-source-8e5744b4ac1b806d84300041
    resource: repo://apps/showcase/tests/weekly-insights-pages.test.ts
  - id: openwiki-source-0790ba7e8a15c95a134e6b3f
    resource: repo://apps/showcase/utils/title-search.ts
generated: { by: "codex", at: "2026-10-10T15:06:52.784Z" }
verified:
  - by: openwiki/0.6.0
    at: 2026-10-10T15:06:52.784Z
---

# Nuxt Showcase 使用體驗與資料快取

Nuxt Showcase 是成果的唯讀瀏覽介面。首頁由 server-side `useFetch` 取得列表，詳細頁同樣在 server 階段取得單筆內容；Notion credentials 與呼叫均留在 Nitro server routes，瀏覽器只接觸 `/api/showcase/*`。

此頁負責瀏覽行為、畫面狀態與快取；Notion schema 和跨應用資料契約見[Notion 資料整合](../integrations/notion-and-showcase.md)，週報作者的整理、進度與建置流程見[每週回顧整理與內容發布流程](../workflows/weekly-insights.md)。

## 列表與詳細頁

首頁先去重，再以標題做 client-side、繁簡字元等價且不分大小寫的搜尋，並將未讀項目排在已讀項目前。列表可一次標記目前篩選集合為已讀。詳細頁成功取得資料後，會把 Notion page id 與穩定 read key 一併標記，並以 Markdown renderer 顯示 block content；有效 YouTube URL 另產生 privacy-enhanced embed。

首頁和詳細頁都處理 loading、error 與 hydration。詳細頁在沒有 loading、沒有 fetch error 且沒有 item 時產生 404。頁面 title、description 與 social metadata 會跟隨結果內容更新。

## 每週回顧

`/insights` 以已發布週報呈現整體觀察、分類洞見與統計篩選；`/insights/{週日日期}` 顯示單週正文、完整程度、分類統計及代表來源。篩選週次、分類與是否納入部分週會更新 URL query；單週頁提供前後週導覽。內容由 repository 週報文件建置，頁面經 server API 讀取，不會在瀏覽時呼叫 LLM 或即時查詢 Notion。

Overview 也可顯示固定的話題演變紀錄：每個話題列出已核對完整週的摘要、連到相應單週回顧，並標示後續觀察方向；分類洞見則連到相關話題。這些紀錄不隨週次篩選改寫，未列出的週不表示話題消失。

## 已讀狀態與選用同步

已讀紀錄以 Nuxt `useState` 保留 session 記憶體狀態，並在 browser 可用時同步到 `localStorage`；SSR 階段不讀取 browser API。資料會驗證 shape、合併跨 navigation 狀態，並只保留最近 500 筆。storage quota 或 privacy mode 失敗不阻止本次 session 的 in-memory 行為。

首頁提供前往 `/settings/sync` 的入口，由該頁的 `ReadSyncControl` 輸入個人同步碼連結裝置。取得 HttpOnly session 後，瀏覽器透過 Nuxt 私人 API 與 Upstash 同步 read/unread；有效 session 會在頁面載入時自動恢復，遠端故障時保留本機狀態。詳細的驗證、合併與儲存語意見[跨裝置已讀同步](read-state-sync.md)。

首頁在 mounted、activated、focus、重新變為 visible、返回 list route，以及 BFCache `pageshow` 時重新同步已讀狀態。這些事件也會在 server response 已超過自己的 `cache_ttl_seconds` 時觸發資料刷新。

## Server SWR cache

列表 route 使用單一 cache，詳細 route 則依 Notion page id 各有 cache；TTL 改變時會重建相應 cache。一般 `get` 的語意如下：

- fresh snapshot：立即回傳，不呼叫 fetcher；
- stale snapshot：立即回傳舊值並在背景更新，同時共用既有的 in-flight refresh；
- 沒有 snapshot：等待第一次 fetch，失敗則向上拋出；
- 背景更新失敗且已有 snapshot：保留舊值。

首頁使用 `?refresh=1` 明確要求 `cache.refresh`，response 設為 `Cache-Control: no-store`。forced refresh 不共用既有背景 refresh，並以遞增 refresh id 確保較晚啟動的 refresh 才能覆寫 snapshot；因此較慢結束的舊 request 不會蓋掉較新的資料。route 最外層仍以 `peek()` 作 Notion 暫時失敗的 fallback；完全沒有 snapshot 時才回 502。

Browser 端 stale refresh 也會去重同時請求。若 forced refresh 失敗，現有列表保持可見，不以錯誤覆寫畫面。

## 搜尋高亮與安全排錯

標題搜尋透過 opencc-js 的 TSCharacters 字元字典正規化繁簡字與大小寫，不將「影片／視頻」或「人工智慧／人工智能」視為同義詞。搜尋為 literal substring，正規表示式符號也視為一般字元。預處理保留原始字元的 UTF-16 offset；HighlightedTitle 以 Vue 文字插值與 mark 呈現命中範圍，維持原標題、不使用 v-html。

公開 diagnostics 與 health API 已移除，首頁錯誤區塊也不再提供診斷連結。列表與詳情使用固定一般錯誤訊息，不把設定 snapshot 或原始 Notion 錯誤傳給訪客；缺少設定為 500，上游失敗且沒有快取為 502。server log 只記錄設定存在與否或預定義錯誤類型，背景更新失敗也會記錄。Nitro error hook 對展示列表、詳情與每週回顧頁/API 的 4xx、5xx 最終回應補上 Cache-Control: no-store，成功回應維持各 route 的既有快取。排錯方式見[設定、執行與部署](../operations/configuration-and-deployment.md)。

## 延伸閱讀

- [系統架構與端到端資料流](../architecture/system-overview.md)
- [Notion 資料整合](../integrations/notion-and-showcase.md)
- [跨裝置已讀同步](read-state-sync.md)
- [設定、執行與部署](../operations/configuration-and-deployment.md)
- [開發規則與測試策略](../operations/development-and-testing.md)
