---
type: frontend
title: Streamlit 任務操作與狀態導覽
description: 說明 Streamlit 新增任務、列表與詳細頁、SQLite 瀏覽歷史及 RSS 操作的資料邊界，並導向 API 與任務生命週期文件。
tags: [streamlit, tasks, history, rss, frontend]
verified:
  - by: openwiki/0.6.0
    at: 2026-10-10T15:06:52.784Z
sources:
  - id: openwiki-source-7332ded4af4c5b8186446177
    resource: repo://apps/whisper_summary/apps/ui/streamlit_app.py
  - id: openwiki-source-fe5f0de19ee909f2cb957b09
    resource: repo://apps/whisper_summary/apps/ui/ui_api.py
  - id: openwiki-source-d546965546d2543cd3b8366e
    resource: repo://apps/whisper_summary/apps/ui/ui_history.py
  - id: openwiki-source-c4f2e43a1ad54892949d8334
    resource: repo://apps/whisper_summary/apps/ui/ui_rss.py
  - id: openwiki-source-d1b4251279ceac6c8afea51e
    resource: repo://apps/whisper_summary/apps/ui/ui_views.py
generated: { by: "codex", at: "2026-10-10T15:06:52.784Z" }
---

# Streamlit 任務操作與狀態導覽

Streamlit 是本機操作者介面，以 `make streamlit` 啟動。入口 `apps/whisper_summary/apps/ui/streamlit_app.py` 依 session 中是否有 `selected_task_id` 切換主畫面與詳細頁；選取的 database 另存於 `selected_db_choice`，避免與主畫面的 widget key 衝突。

## 操作與資料邊界

| 操作 | 資料路徑 |
| --- | --- |
| 新增 URL | 正規化與驗證 YouTube URL，再透過 `ui_api.py` 呼叫 `POST /tasks` |
| 背景處理與重試 | 透過 API 提交操作；實際處理由 worker 執行 |
| 任務列表 | `ui_views.py` 透過 composition 建立所選 repository，直接讀取 tasks |
| RSS 管理 | 僅 SQLite 支援；直接使用 RSS repository 與 subscription service |
| 最近瀏覽 | 寫入 SQLite history，再更新 Streamlit session 中的顯示資料 |

因此 Streamlit 並非所有讀寫都經 HTTP。部署時除了 API 連線，也要核對 UI 所使用的 database 路徑與設定。API payload、認證與 client 相容性以[HTTP API 與 Client 契約](../interfaces/http-api-and-clients.md)為準；worker、lease 與重試語意以[任務生命週期與併發控制](../workflows/task-lifecycle.md)為準。

新增任務可選 SQLite／Notion，以及跟隨系統預設、legacy 或 LangGraph 引擎。API 回應 201 時清空輸入；409 以提示呈現，連線錯誤保留輸入並顯示錯誤。介面送出的引擎選擇是 task override，實際引擎解析見[媒體转錄與摘要流程](../workflows/media-processing.md)。

## 列表與詳細頁

列表以建立時間由新到舊排序，預設顯示 Pending、Processing、Completed 與 Failed；狀態選項另含 Failed Retry Created。每頁可選 20、50 或 100 筆，分頁在狀態篩選之後進行。列表顯示 Taipei 時間、引擎、完成耗時、Notion 入口與操作按鈕。

點擊 View 會記錄最近瀏覽、保存 task 與 database 選擇，再重新執行進入詳細頁。Notion 按鈕同樣記錄瀏覽；無效或缺少連結以提示呈現。Failed 任務提供 API retry 入口。修改列表時優先檢查 `ui_tasks.py` 的排序與篩選，以及 `ui_notion.py` 的連結顯示邏輯。

## 瀏覽歷史與 RSS

`ui_history.py` 將 task id 與瀏覽時間持久化於 SQLite，讀取時按設定的 TTL 清理，再同步至 session state。此歷史獨立於 Showcase 的 localStorage／Upstash 已讀同步；兩者不能視為同一份狀態。SQLite 歷史的去重、排序與清理有 `test_recent_history.py` 覆蓋。

RSS 管理支援新增、編輯、啟停、刪除與手動 poll。手動 poll 由 `ui_rss.py` 建立 monitor 並呼叫 `poll_once()`；首次監控只建立 watermark，不補抓歷史影片。RSS 狀態與失敗恢復見[YouTube RSS 自動化](../workflows/rss-automation.md)。

## 修改與驗證入口

- 畫面與導航：`ui_views.py`、`streamlit_app.py`。
- HTTP 操作與管理操作：`ui_api.py`、`ui_processing.py`；先核對 API 契約。
- 列表與歷史：`test_task_status_filter.py`、`test_recent_history.py` 與 Streamlit integration tests。
- RSS：`test_ui_rss.py`；先核對 subscription service 與 monitor 行為。

啟動、環境與 Docker 設定見[設定、執行與部署](../operations/configuration-and-deployment.md)；儲存責任見[任務、鎖與結果持久化](../persistence/task-and-result-storage.md)。
