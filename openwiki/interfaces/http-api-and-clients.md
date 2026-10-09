---
type: interface-guide
title: HTTP API 與客戶端整合
description: 說明 FastAPI feature routers、task queue 回應、RSS 與 processing lock API，以及各 client 邊界。
tags: [api, fastapi, clients, rss, processing-lock]
sources:
  - id: openwiki-source-3f302af29bc8e91334af86aa
    resource: repo://apps/browser-extension/service_worker.js
  - id: openwiki-source-6b47ec2bb946dbfe3f605cea
    resource: repo://apps/showcase/README.md
  - id: openwiki-source-8de160800c7fe6a0417a5cac
    resource: repo://apps/showcase/server/api/showcase/insights/%5Bstart%5D.get.ts
  - id: openwiki-source-f987324e0612a557c62a85fb
    resource: repo://apps/showcase/server/api/showcase/results.get.ts
  - id: openwiki-source-f1a67212459cd418a8f6d3d6
    resource: repo://apps/showcase/server/api/showcase/results/%5Bid%5D.get.ts
  - id: openwiki-source-98886cf9c4725ca201459fa1
    resource: repo://apps/showcase/server/plugins/showcase-error-cache.ts
  - id: openwiki-source-1733e19cd888bc4a90558aa4
    resource: repo://apps/whisper_summary/apps/api/dependencies.py
  - id: openwiki-source-8a8f27feb31a478f83017412
    resource: repo://apps/whisper_summary/apps/api/routers/processing.py
  - id: openwiki-source-47e37d76faef3db362599ed8
    resource: repo://apps/whisper_summary/apps/api/routers/rss.py
  - id: openwiki-source-2f9fce5f97d840294b957a0b
    resource: repo://apps/whisper_summary/apps/api/routers/tasks.py
  - id: openwiki-source-e8a3e4e8f72c5329a78957ec
    resource: repo://apps/whisper_summary/apps/api/schemas.py
  - id: openwiki-source-fe5f0de19ee909f2cb957b09
    resource: repo://apps/whisper_summary/apps/ui/ui_api.py
  - id: openwiki-source-5d30f93453a5fc9227aa0b47
    resource: repo://apps/whisper_summary/services/pipeline/processing_runner.py
  - id: openwiki-source-daab87d344d0f6ce8a388ee8
    resource: repo://apps/whisper_summary/services/rss/channel_monitor.py
  - id: openwiki-source-5862fc4af2e29ada3e6abb6a
    resource: repo://apps/whisper_summary/services/rss/subscription_service.py
  - id: openwiki-source-4ef6c51002fe401d434edeb5
    resource: repo://apps/whisper_summary/services/tasks/processing_scheduler.py
generated: { by: "codex", at: "2026-10-09T15:26:03.952Z" }
verified:
  - by: openwiki/0.6.0
    at: 2026-10-09T15:26:03.952Z
---

# HTTP API 與客戶端整合

`whisper_summary.apps.api.main` 只建立 FastAPI app 並註冊 task、RSS 與 processing routers。Streamlit、Browser Extension 和 RSS monitor 是 API clients；Nuxt Showcase 不呼叫 Task API，而由 server route直接查詢 Notion。

## Task API

`POST /tasks` 驗證並正規化 YouTube URL，依 backend 執行去重。新 task 回 201；TTL 內 Completed cache 回 200；active或依 policy阻擋的 duplicate回409。新 task只進入 persisted queue，response以 `processing_started=false` 說明由 dedicated processing worker處理。

建立請求可帶 `processing_engine: legacy|langgraph` 覆寫該 task 的執行引擎；未指定時 worker 使用 `PROCESSING_ENGINE` 設定。

`POST /tasks/retry` 只接受 Failed task，建立新的 Pending retry並更新來源狀態；同樣由 dedicated worker後續取得。API process不啟動 daemon thread。

`POST /processing-jobs` 現在是 dedicated-worker mode 的確認端點：驗證 backend設定後回202，告知 persisted queue會被專用 worker輪詢，不負責取得 lock或啟動執行緒。

## Worker queue 與 lease API

專用 worker 以 `X-Worker-Token` 呼叫 SQLite queue：`POST /worker-tasks/claim` 取得 task 與 lease token，沒有待處理 task 回 204；heartbeat、progress、complete、fail 端點都驗證 worker id 與 lease token。Lease 已失效時回 409，worker 不再寫入該 task。未設定 worker token 回 503，缺少或錯誤 token 分別回 401／403。

維運者以 `X-Maintainer-Token` 讀取 `GET /processing-leases`，必要時對單筆 task 呼叫 `POST /processing-leases/{task_id}/fail`；後者支援 dry run、預期 worker 比對及強制失效的 age threshold。

## RSS 與維運 API

`POST /rss/subscriptions` 驗證 channel input並建立 SQLite subscription，成功回201，duplicate回409。Processing lock GET/DELETE要求 `X-Maintainer-Token`；未設定 server token、缺 header與錯誤 token分別回503、401、403。DELETE支援 expected worker、force age threshold與 dry run snapshots。

Browser Extension只使用 task與RSS endpoints，不提供 lock管理。Streamlit的 HTTP helpers設定 timeout並把 transport/JSON錯誤轉成可呈現訊息；RSS monitor建立 task但不直接執行media pipeline。

相關閱讀：[任務生命週期](../workflows/task-lifecycle.md)、[Browser Extension](../integrations/browser-extension.md)。

## Showcase 每週洞察 API

`GET /api/showcase/insights` 回傳系列與週次摘要；`GET /api/showcase/insights/{start}` 回傳單週內容與前後週 slug。兩者對成功回應設定 300 秒 shared cache 與 ETag。不存在的週報回 404 並設 `no-store`。資料從建置時產生的 registry 讀取，不即時呼叫 Notion。

## Showcase API 錯誤契約

Showcase 的 GET 列表與詳情正常回應及快取備援保持原有格式。必要 Notion 設定缺少時回 500，statusMessage 為 `Showcase service is unavailable.`；上游失敗且沒有 snapshot 時回 502，列表為 `Failed to load showcase results.`，詳情為 `Failed to load showcase detail.`。詳情 handler 缺少 id 時仍回 400。

這些對外訊息不包含原始 Notion 錯誤或 env snapshot。展示 API 的錯誤回應使用 `Cache-Control: no-store`；Nitro error hook 也涵蓋 results 與 weekly insights 頁面/API，補上 SWR 代理回應可能遺失的標頭。公開的 `/api/showcase/diagnostics` 與 `/api/showcase/health` 已移除，不再是可用 API；排錯使用部署平台 server log 與本機設定檢查。
