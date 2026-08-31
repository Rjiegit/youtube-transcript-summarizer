---
type: integration-workflow
title: YouTube RSS 自動化
description: 說明 YouTube channel 訂閱、watermark polling、API 入列與 monitor 執行模式。
tags: [rss, youtube, automation, sqlite]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-31T13:51:03.458Z
sources:
  - id: openwiki-source-c79e0b87395cb78682a64778
    resource: repo://src/apps/workers/rss_monitor.py
  - id: openwiki-source-3b279564fbfb5cc9e5b4304d
    resource: repo://src/infrastructure/persistence/sqlite/rss_subscription_repository.py
  - id: openwiki-source-0b294e3f86f4bc3838cb6ca2
    resource: repo://src/services/rss/channel_monitor.py
  - id: openwiki-source-25648eab61c0e46bdd2d19af
    resource: repo://src/services/rss/subscription_service.py
  - id: openwiki-source-01f22608fdc3c845dfb0f335
    resource: repo://tests/test_rss_monitor.py
generated: { by: "codex", at: "2026-08-31T13:51:03.458Z" }
---

# YouTube RSS 自動化

RSS 子系統把「發現影片」與「處理影片」分開：monitor 只解析 feed 並呼叫 FastAPI 建立 SQLite task，下載、轉錄與摘要仍由既有 background worker 負責。

## 訂閱與儲存

訂閱輸入可為 YouTube channel id 或 feed URL，service 會正規化兩者並驗證是否一致。SQLite repository 保存 enabled、最後處理的發布時間、最後檢查時間、狀態與錯誤；channel uniqueness violation 會轉成可理解的 duplicate 訊息。polling 只載入 enabled subscriptions。

## Polling 流程

Feed client 以 15 秒 HTTP timeout 取得 Atom XML，解析 video id、title、link、published/updated timestamps，丟棄缺少有效 published time、URL 或 video id 的 entry，最後按發布時間由舊到新排序。

每個訂閱第一次 poll 若尚無 watermark，只把 feed 最新發布時間寫成 `last_processed_published_at` 並標記 `seeded`，完全不建立歷史 tasks。後續 poll 僅處理 `published_at` 嚴格晚於 watermark 的項目。

新項目透過 `POST /tasks` 送出固定的 `db_type=sqlite`、`source_type=rss`、channel id 與 `completed_task_policy=block_existing`。201 計為新 task，409 計為 duplicate；其他狀態視為 poll error。成功處理一批後 watermark 前進到最新新項目。任一例外會保留舊 watermark，記錄該訂閱的 error 與 checked time，讓下一次 poll 可以重試而不漏資料。

## 執行模式與設定

CLI 啟動時先檢查 `RSS_MONITOR_ENABLED`；停用時不 polling。`--once` 執行一輪後輸出結果，否則常駐迴圈。實際 interval 為 `max(RSS_MONITOR_POLL_INTERVAL_SECONDS, RSS_MONITOR_MIN_POLL_INTERVAL_SECONDS)`，API timeout 由 `RSS_MONITOR_TASK_TIMEOUT_SECONDS` 控制，API base URL 由 `TASK_API_BASE_URL` 控制。

Docker Compose 的 rss-monitor 使用 `http://api:8080`，並與 API/Streamlit 共用 repository volume，因此使用同一 SQLite database。RSS monitor 本身不支援 Notion queue。

## 延伸閱讀

- [Browser Extension 任務與 RSS 入口](browser-extension.md)
- [HTTP API 與 Client 契約](../interfaces/http-api-and-clients.md)
- [任務、鎖與結果持久化](../persistence/task-and-result-storage.md)
- [任務生命週期與併發控制](../workflows/task-lifecycle.md)
- [設定、執行與部署](../operations/configuration-and-deployment.md)
