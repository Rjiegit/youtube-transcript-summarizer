---
type: integration
title: Notion 資料整合與 Showcase 邊界
description: 說明 Python 的 Notion queue/摘要寫入與 Nuxt Showcase 唯讀查詢、schema 映射及可見性邊界。
tags: [notion, integration, persistence, showcase]
sources:
  - id: openwiki-source-7c8ae95541eb7e7de0873e3d
    resource: repo://apps/showcase/server/utils/notion.ts
  - id: openwiki-source-71c6fb5bae534b32dd19c0ab
    resource: repo://src/infrastructure/persistence/notion/client.py
  - id: openwiki-source-5858a6e533d57781fe90f469
    resource: repo://src/infrastructure/storage/summary_storage.py
generated: { by: "codex", at: "2026-09-07T14:09:43.292Z" }
verified:
  - by: openwiki/0.4.3
    at: 2026-09-07T16:12:01.072Z
---

# Notion 資料整合與 Showcase 邊界

Notion 在本系統有兩種不同角色：Python `NotionDB` 可把 database 當作任務 queue；`SummaryStorage` 另建立承載完整摘要 blocks 的成果 page。Nuxt Showcase 不建立或更新資料，只用 server-side API 讀取 database schema、完成項目與 page blocks。

<!-- openwiki: broken internal link [../persistence/task-and-result-storage.md] file "../persistence/task-and-result-storage.md" does not exist. Fix the href or restore the target, then delete this comment. -->
本頁聚焦 Python 與 Nuxt 之間的 Notion schema contract；SQLite transaction、task leases、recent history 與檔案 artifacts 集中在[任務、鎖與結果持久化](../persistence/task-and-result-storage.md)。

## Python 寫入端

<!-- openwiki: broken internal link [../persistence/task-and-result-storage.md] file "../persistence/task-and-result-storage.md" does not exist. Fix the href or restore the target, then delete this comment. -->
Python 有兩條 Notion 寫入路徑：`NotionDB` 以 `URL`、`Name`、`Status` 等 properties 管理 task；`SummaryStorage` 建立含 `Title`、`URL`、`Model`、`Public` 與摘要 blocks 的成果 page。兩者共用 credentials/database 設定，但用途與 schema 不完全相同。Queue locking、rich-text chunking 與 storage failure 語意集中在[任務、鎖與結果持久化](../persistence/task-and-result-storage.md)。

## Nuxt 唯讀端

Showcase 每次查詢先讀 database schema。欄位解析會按已知中英文候選名稱與型別尋找 title、summary、URL、created time/date 與 processing duration，title/created time 另可 fallback 到首個相符型別。缺少欄位時回傳安全預設，例如 `Untitled result`、空 summary 或 `null` URL。

狀態欄位可由設定明確指定；未指定時依 `Status`、` 狀態 `、`State` 等候選尋找 `status`/`select`，最後 fallback 到任一相符型別。指定的欄位不存在或型別錯誤會明確失敗。完全找不到狀態欄位時不加 filter；因此公開 database 若依賴 Completed 可見性，應明確配置正確欄位，而不能把無 filter fallback 當成存取控制。

列表 query 依 created time 倒序、最多 50 筆，通常以解析出的狀態欄位篩選 `Completed`。詳細頁讀取 page properties，並從 page 的 children endpoint 分頁抓取 blocks；每一層遇到 `has_children` 的 block，會再以該 block id 遞迴抓取並分頁完成其 children，形成完整 block tree。這個流程是逐層、依 API 回傳順序進行，任一層的 Notion request 失敗都會讓詳細頁查詢失敗，而不會回傳不完整樹。

完整 block tree 再轉成 Markdown。一般子內容接在 parent 後方；bulleted/numbered list item 與 to-do 的子內容縮排四個 spaces，以保存巢狀清單層級；quote 與 callout 則將自己的文字和所有子內容一起套用引用前綴。若 parent block 本身沒有可呈現內容，仍保留其可呈現 children。只有整棵 block tree 最終沒有 Markdown content 時，詳細頁才 fallback 到 Summary property。

## 安全與故障邊界

- Notion token 只存在 Python process 或 Nuxt Nitro server；browser 不直接呼叫 Notion。
- diagnostics 僅回報設定是否存在，不回傳 token value。
- Showcase 將 Notion error body 壓成單行並截到 300 characters 後才放入錯誤訊息，避免無界輸出。
- Showcase cache 可在短暫 Notion failure 時回傳最後成功 snapshot，但初次查詢沒有 snapshot 時仍會失敗。
- Notion queue 與 SQLite 的 consistency 差異由持久化頁維護，本頁不把 Showcase 的 read schema 誤當作 queue locking 保證。

## 延伸閱讀

- [任務、鎖與結果持久化](../architecture/task-and-result-storage.md)
- [媒體轉錄與摘要流程](../workflows/media-processing.md)
- [Nuxt Showcase 使用體驗與資料快取](showcase-experience.md)
- [設定、執行與部署](../operations/configuration-and-deployment.md)
