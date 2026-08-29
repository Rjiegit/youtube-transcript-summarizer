---
type: quickstart
title: 快速開始與導覽
description: 從環境設定、安裝、啟動與測試開始，並依開發任務導向相關系統文件。
tags: [quickstart, setup, navigation]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-29T14:03:31.952Z
sources:
  - id: openwiki-source-e201e686a785f09b6d899f0b
    resource: repo://compose.yaml
  - id: openwiki-source-27a43165fe079c2f44e8c6f5
    resource: repo://frontend/nuxt-showcase/package.json
  - id: openwiki-source-012f2c78e3b1446dfc35803f
    resource: repo://Makefile
  - id: openwiki-source-05ccef8d4cf1698187f20464
    resource: repo://pyproject.toml
  - id: openwiki-source-526d4ed1a7d9ebdeb9c244a6
    resource: repo://src/core/config.py
generated: { by: "codex", at: "2026-08-29T14:03:31.952Z" }
---

# 快速開始與導覽

這個 repository 包含 Python 3.14 的 YouTube 轉錄/摘要平台，以及 `frontend/nuxt-showcase` 的獨立 Nuxt 3 成果展示站。Python 側提供 FastAPI、Streamlit、queue worker 和 RSS monitor；Nuxt 側直接由 server routes 讀取 Notion。

## 最短本機啟動路徑

在 repository root：

```bash
cp .env.example .env
uv sync --frozen --no-install-project
make api
```

另開 terminal 啟動 Streamlit：

```bash
make streamlit
```

API 預設為 `http://localhost:8080`，Streamlit 預設為 `http://localhost:8501`。`.env` 至少提供一個可用的摘要 provider key；實際 pipeline 會寫入 Notion，因此正常處理也需要 `NOTION_API_KEY` 與 `NOTION_DATABASE_ID`。不要提交 `.env`。

建立 task 後 API 通常會自動排程 background worker；也可手動同步 drain SQLite queue：

```bash
make run
```

## Docker 啟動

```bash
docker compose up -d
```

這會啟動 API、Streamlit 與 RSS monitor。API container 啟動時預設更新 yt-dlp；不希望啟動時存取下載來源可設定 `YTDLP_AUTO_UPDATE=0`。RSS monitor 還需 `RSS_MONITOR_ENABLED=true` 才會實際 polling。

## Nuxt Showcase

```bash
cd frontend/nuxt-showcase
npm install
npm run check-env
npm run dev
```

開發站預設在 `http://localhost:3000`。必要設定為 Notion token 與 database id，可放在 frontend `.env` 或 repository root `.env`；標準 `NOTION_*` 名稱優先於相容的 `NUXT_*` 名稱。Showcase 是唯讀介面，不會啟動 Python processing pipeline。

## 驗證變更

在 repository root 執行 Python suite 與 lint：

```bash
make test
uv run flake8 .
```

執行 Nuxt suite 與 production build：

```bash
npm --prefix frontend/nuxt-showcase run test
npm --prefix frontend/nuxt-showcase run build
```

## 依任務找文件

| 你要做的事 | 文件 |
| --- | --- |
| 了解元件責任與跨系統資料流 | [系統架構總覽](architecture/system-overview.md) |
| 修改 task API、dedup、retry 或 locks | [任務生命週期與併發控制](workflows/task-lifecycle.md) |
| 修改下載、Whisper、LLM 或輸出 | [媒體轉錄與摘要流程](workflows/media-processing.md) |
| 維護 RSS channel automation | [YouTube RSS 自動化](integrations/rss-automation.md) |
| 修改 Notion schema 或 Python/Nuxt 整合 | [Notion 資料整合](integrations/notion-and-showcase.md) |
| 修改 Showcase UX、read state 或 SWR | [Nuxt Showcase 使用體驗與資料快取](frontend/showcase-experience.md) |
| 設定 Docker、env、cache 或部署 | [設定、執行與部署](operations/configuration-and-deployment.md) |
| 新增或定位測試 | [測試策略與擴充指南](testing/test-strategy.md) |

## 常見檢查

- Showcase 顯示缺少設定：先執行 `npm run check-env`，再查看 `/api/showcase/diagnostics`。
- diagnostics 正常但無資料：查看 `/api/showcase/health`，確認 Notion integration 權限、database id 與 status schema。
- task 已 Pending 但未開始：呼叫 `POST /processing-jobs` 或執行 `make run`；先確認是否已有 processing lock。
- RSS 沒有建立舊影片 tasks：首次 poll 只 seed watermark，這是避免回填整個歷史 feed 的預期行為。
