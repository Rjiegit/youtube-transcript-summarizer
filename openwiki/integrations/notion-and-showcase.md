---
type: integration
title: Notion 資料整合
description: 說明 Python 的 Notion queue/摘要寫入與 Nuxt Showcase 唯讀查詢、schema 映射及可見性邊界。
tags: [notion, integration, persistence, showcase]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-29T14:03:31.952Z
sources:
  - id: openwiki-source-59891cd71dd0c8a50b5690a9
    resource: repo://frontend/nuxt-showcase/server/utils/notion.ts
  - id: openwiki-source-71c6fb5bae534b32dd19c0ab
    resource: repo://src/infrastructure/persistence/notion/client.py
  - id: openwiki-source-d8184485d0e13f57f6ff767d
    resource: repo://src/infrastructure/persistence/notion/utils.py
  - id: openwiki-source-5858a6e533d57781fe90f469
    resource: repo://src/infrastructure/storage/summary_storage.py
generated: { by: "codex", at: "2026-08-29T14:03:31.952Z" }
---

# Notion 資料整合

Notion 在本系統有兩種不同角色：Python `NotionDB` 可把 database 當作任務 queue；`SummaryStorage` 另建立承載完整摘要 blocks 的成果 page。Nuxt Showcase 不建立或更新資料，只用 server-side API 讀取 database schema、完成項目與 page blocks。

## Python 寫入端

`NotionDB` 使用 `NOTION_API_KEY` 與 `NOTION_DATABASE_ID`，以 `URL`、`Name`、`Status` 建立任務。查詢 pending tasks 後會 best-effort 將第一筆設為 `Processing`；Notion 沒有真正 row lock，因此此 backend 的 global lock、heartbeat 與 release 都是 no-op，部署上假設單一 worker。

任務完成時可更新 `Name`、`Summary`、`Processing Duration` 與錯誤資訊。獨立的 `SummaryStorage` 則建立含 `Title`、`URL`、`Model` 與預設為 `false` 的 `Public` 欄位，摘要本文分割成 paragraph children。rich text 以 1,800 characters 分塊，避免超過 Notion 限制。

`SummaryStorage` 只有在 Streamlit flag、`APP_ENV=test` 或 `FORCE_TEST_MODE` 明確啟用時走 mock；內容中的關鍵字不會誤觸測試模式。實際 Notion exception 會記錄後重新拋出，讓 processing worker 將 task 標記為 `Failed`。

## Nuxt 唯讀端

Showcase 每次查詢先讀 database schema。欄位解析會按已知中英文候選名稱與型別尋找 title、summary、URL、created time/date 與 processing duration，title/created time 另可 fallback 到首個相符型別。缺少欄位時回傳安全預設，例如 `Untitled result`、空 summary 或 `null` URL。

狀態欄位可由設定明確指定；未指定時依 `Status`、`狀態`、`State` 等候選尋找 `status`/`select`，最後 fallback 到任一相符型別。指定的欄位不存在或型別錯誤會明確失敗。完全找不到狀態欄位時不加 filter；因此公開 database 若依賴 Completed 可見性，應明確配置正確欄位，而不能把無 filter fallback 當成存取控制。

列表 query 依 created time 倒序、最多 50 筆，通常以解析出的狀態欄位篩選 `Completed`。詳細頁讀取 page properties，並分頁抓取所有 child blocks；支援的 blocks 轉成 Markdown，若沒有 block content 才 fallback 到 Summary property。

## 安全與故障邊界

- Notion token 只存在 Python process 或 Nuxt Nitro server；browser 不直接呼叫 Notion。
- diagnostics 僅回報設定是否存在，不回傳 token value。
- Showcase 將 Notion error body 壓成單行並截到 300 characters 後才放入錯誤訊息，避免無界輸出。
- Showcase cache 可在短暫 Notion failure 時回傳最後成功 snapshot，但初次查詢沒有 snapshot 時仍會失敗。
- Notion queue 的單 worker 假設不同於 SQLite 的真實 processing/task locks；若需要併發 worker，應使用 SQLite 或新增具原子鎖能力的 adapter。

## 延伸閱讀

- [媒體轉錄與摘要流程](../workflows/media-processing.md)
- [Nuxt Showcase 使用體驗與資料快取](../frontend/showcase-experience.md)
- [設定、執行與部署](../operations/configuration-and-deployment.md)
