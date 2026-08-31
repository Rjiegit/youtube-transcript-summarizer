---
type: integration
title: Browser Extension 任務與 RSS 入口
description: 說明 Manifest V3 extension 如何辨識 YouTube context、建立摘要任務或 RSS 訂閱，以及設定、權限與失敗回饋。
tags: [browser-extension, chrome, youtube, api, rss]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-31T13:51:03.458Z
sources:
  - id: openwiki-source-c297a6919354a0aef232d787
    resource: repo://src/apps/extension/content_script.js
  - id: openwiki-source-224f65803d3de46b7fae180b
    resource: repo://src/apps/extension/manifest.json
  - id: openwiki-source-48e217db31524d96d35dbecd
    resource: repo://src/apps/extension/options.js
  - id: openwiki-source-0520e948964d45782d02b5a3
    resource: repo://src/apps/extension/service_worker.js
generated: { by: "codex", at: "2026-08-31T13:51:03.458Z" }
---

# Browser Extension 任務與 RSS 入口

Browser Extension 是 FastAPI 的 public client，讓使用者不必複製 URL。它不保存 task、不執行 processing pipeline，也不持有 Notion 或 LLM credentials；唯一的 server 設定是使用者可修改的 API base URL。

## 組成與權限

`src/apps/extension` 是可直接載入 Chrome/Edge 的 Manifest V3 extension：

- service worker 建立 context menus、處理 toolbar action、呼叫 FastAPI 並顯示 badge/notification；
- content script 在 YouTube DOM 中找 channel id、channel title 與 page type；
- options page 驗證並保存 API base URL；
- `chrome.storage.sync` 讓設定跨瀏覽器 profile 同步。

Manifest 要求 `storage`、`contextMenus`、`activeTab`、`tabs` 與 `notifications`，並宣告 `*://*/*` host permission。內容腳本只注入 YouTube watch、shorts、live、channel 與 handle pages，但廣泛 host permission 讓 service worker 能呼叫使用者設定的任意 HTTP/HTTPS API host。這是部署時應審查的 client trust boundary。

## 影片任務路徑

工具列按鈕會先詢問 content script 的 page context：channel page 轉向 RSS 訂閱，其他頁面送出摘要任務。右鍵選單則分開提供「送出目前 YouTube page」與「送出選取的 YouTube link」。

送出任務前，service worker 只接受 YouTube watch、shorts、live 或 `youtu.be` URL。通過檢查後，它從 storage 取得 API base URL，向 `POST /tasks` 傳送：

```json
{
  "url": "<youtube-url>",
  "db_type": "sqlite"
}
```

201 被視為成功；其他 status 會優先顯示 API 的 `detail` 或 `message`。每次 request 以 `AbortController` 設定 10 秒 timeout。成功與失敗都用 extension notification 及暫時的 `OK`／`ERR` badge 回饋，不會在 browser 端輪詢後續 processing 狀態。

## Channel 與 RSS 訂閱路徑

content script 先從 `meta[itemprop=channelId]` 取得 channel id，找不到時解析頁面的 Atom alternate link；title 依序使用 Open Graph title、title meta、頁首文字，最後 fallback 到 channel id。page type 由 pathname 判定。

service worker 若無法與 content script 通訊，會再從 URL 做有限 fallback：`/channel/<id>` 可直接取得 channel id，`/@handle` 只能提供 display title，不能自行解析真正的 channel id。因此 handle page 若 DOM 沒有可用 metadata，訂閱會以「無法偵測 channel ID」失敗，而不是送出猜測值。

取得 channel context 後，Extension 呼叫 `POST /rss/subscriptions`，傳送 channel id、title 與 `enabled: true`。201 表示建立成功，409 顯示 duplicate；其他 status 或 10 秒 timeout 轉成通知。實際 feed URL validation、SQLite persistence 與 polling 都由 Python API/RSS monitor 負責。

## 設定與安全界線

API base URL 預設是 `http://localhost:8080`。Options page 只接受可由 `URL` 解析且 protocol 為 HTTP/HTTPS 的值，保存前不測試 connectivity，也不附 authentication token。若 API 暴露到非本機環境，TLS、CORS/網路存取政策與 task submission protection 必須由部署層處理；Extension 目前只對 processing lock 等管理端點完全不提供操作能力。

開發安裝使用瀏覽器的「載入未封裝項目」指向 `src/apps/extension`。此 repository 目前沒有 extension 專用 automated test suite，因此修改 URL routing、DOM selectors、permissions 或 status handling 時，除 code review 外還需要在 Chrome/Edge 手動驗證影片頁、列表 link、channel page、timeout、duplicate 與無法偵測 channel 等情境。

## 延伸閱讀

- [HTTP API 與 Client 契約](../interfaces/http-api-and-clients.md)
- [YouTube RSS 自動化](rss-automation.md)
- [系統架構與端到端資料流](../architecture/system-overview.md)
- [快速開始與開發導覽](../quickstart.md)
