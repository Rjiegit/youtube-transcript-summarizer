---
type: integration
title: HTTP API 與客戶端整合
description: 說明 FastAPI feature routers、task queue 回應、RSS 與 processing lock API，以及各 client 邊界。
tags: [api, fastapi, clients, rss, processing-lock]
verified:
  - by: openwiki/0.4.3
    at: 2026-09-13T10:51:33.281Z
sources:
  - id: openwiki-source-3f302af29bc8e91334af86aa
    resource: repo://apps/browser-extension/service_worker.js
  - id: openwiki-source-f987324e0612a557c62a85fb
    resource: repo://apps/showcase/server/api/showcase/results.get.ts
  - id: openwiki-source-342c9b983ccf76e13ea1243b
    resource: repo://whisper_summary/apps/api/dependencies.py
  - id: openwiki-source-ad4df8250d444175a5c8ddb3
    resource: repo://whisper_summary/apps/api/routers/processing.py
  - id: openwiki-source-eac8fbc35543484334a727f3
    resource: repo://whisper_summary/apps/api/routers/rss.py
  - id: openwiki-source-d1e2e939cdaa20a1825bddb5
    resource: repo://whisper_summary/apps/api/routers/tasks.py
  - id: openwiki-source-a0e78d9af1e9cc8e35a1baae
    resource: repo://whisper_summary/apps/ui/ui_api.py
  - id: openwiki-source-e66f0503669326252cbeb176
    resource: repo://whisper_summary/services/rss/channel_monitor.py
  - id: openwiki-source-6ddd6777ce5c4b8bba9dcf83
    resource: repo://whisper_summary/services/rss/subscription_service.py
  - id: openwiki-source-8bf1f6c7cf873df06749ede0
    resource: repo://whisper_summary/services/tasks/processing_scheduler.py
generated: { by: "codex", at: "2026-09-13T10:51:33.281Z" }
---

# HTTP API 與客戶端整合

`whisper_summary.apps.api.main` 只建立 FastAPI app 並註冊 task、RSS 與 processing routers。Streamlit、Browser Extension 和 RSS monitor 是 API clients；Nuxt Showcase 不呼叫 Task API，而由 server route直接查詢 Notion。

## Task API

`POST /tasks` 驗證並正規化 YouTube URL，依 backend 執行去重。新 task 回 201；TTL 內 Completed cache 回 200；active或依 policy阻擋的 duplicate回409。新 task只進入 persisted queue，response以 `processing_started=false` 說明由 dedicated processing worker處理。

`POST /tasks/retry` 只接受 Failed task，建立新的 Pending retry並更新來源狀態；同樣由 dedicated worker後續取得。API process不啟動 daemon thread。

`POST /processing-jobs` 現在是 dedicated-worker mode 的確認端點：驗證 backend設定後回202，告知 persisted queue會被專用 worker輪詢，不負責取得 lock或啟動執行緒。

## RSS 與維運 API

`POST /rss/subscriptions` 驗證 channel input並建立 SQLite subscription，成功回201，duplicate回409。Processing lock GET/DELETE要求 `X-Maintainer-Token`；未設定 server token、缺 header與錯誤 token分別回503、401、403。DELETE支援 expected worker、force age threshold與 dry run snapshots。

Browser Extension只使用 task與RSS endpoints，不提供 lock管理。Streamlit的 HTTP helpers設定 timeout並把 transport/JSON錯誤轉成可呈現訊息；RSS monitor建立 task但不直接執行media pipeline。

相關閱讀：[任務生命週期](../workflows/task-lifecycle.md)、[Browser Extension](browser-extension.md)。
