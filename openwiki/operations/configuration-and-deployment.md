---
type: operations-guide
title: 設定、執行與部署
description: 整理 Python 與 Nuxt 的環境設定、啟動指令、Docker topology、診斷與秘密管理。
tags: [operations, configuration, docker, deployment]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-29T14:03:31.952Z
sources:
  - id: openwiki-source-e201e686a785f09b6d899f0b
    resource: repo://compose.yaml
  - id: openwiki-source-a5853bfe60c0ac906f6ab533
    resource: repo://frontend/nuxt-showcase/nuxt.config.ts
  - id: openwiki-source-8c08a854bf0339fc3de677b0
    resource: repo://frontend/nuxt-showcase/scripts/check-env.mjs
  - id: openwiki-source-d3847a8af5c5a244f228a0ca
    resource: repo://frontend/nuxt-showcase/server/utils/config.ts
  - id: openwiki-source-012f2c78e3b1446dfc35803f
    resource: repo://Makefile
  - id: openwiki-source-526d4ed1a7d9ebdeb9c244a6
    resource: repo://src/core/config.py
generated: { by: "codex", at: "2026-08-29T14:03:31.952Z" }
---

# 設定、執行與部署

## Python 主系統

複製 `.env.example` 為 `.env` 並填入所需值，絕不可提交 secrets。摘要至少需要 `OPENAI_API_KEY`、`GOOGLE_GEMINI_API_KEY` 或 `OLLAMA_API_KEY` 之一；使用 Notion 時需同時提供 `NOTION_API_KEY` 與 `NOTION_DATABASE_ID`。Discord、Notion workspace URL、RSS 與 lock admin token 依功能選填。

`Config` 載入 `.env`、固定 Asia/Taipei timezone，並確保 `data/`、`data/videos/`、`data/_summarized/` 存在。RSS 預設停用；poll interval、minimum interval 和 task API timeout 都至少為一秒。

常用入口：

| 目的 | 指令 |
| --- | --- |
| 安裝 frozen Python dependencies | `uv sync --frozen --no-install-project` |
| API | `make api` |
| Streamlit | `make streamlit` |
| SQLite worker 一次 | `make run` |
| RSS monitor | `make rss-monitor` / `make rss-monitor-once` |
| Python tests | `make test` |

`make install` 還會寫入 `/usr/local/bin/yt-dlp`，本機可能需要權限，不應把它視為純 dependency sync。API 的開發命令綁定 `0.0.0.0:8080` 並啟用 reload。

Docker Compose 以同一 image、`.env` 與 bind-mounted repository 啟動 api、streamlit、rss-monitor。API 暴露 8080、Streamlit 暴露 8501；後兩者的 `TASK_API_BASE_URL` 指向 Docker DNS 名稱 `api`。API 啟動時預設更新 yt-dlp，可用 `YTDLP_AUTO_UPDATE=0` 停用。

processing lock 管理端點需 `PROCESSING_LOCK_ADMIN_TOKEN`。`make clear-processing-lock` 會從 environment 或 root `.env` 取 token 並送出 force release；執行前應先用 GET/dry-run 確認目標 backend 與 lock age，避免中斷活躍 worker。

## Nuxt Showcase

在 `frontend/nuxt-showcase` 執行 `npm install`、`npm run dev`、`npm run test`、`npm run build`。`make showcase` 優先載入 frontend `.env`，不存在才使用 repository root `.env`。

Showcase 設定優先序為 runtime config，其次標準 `NOTION_*`/`SHOWCASE_*`，最後相容用的 `NUXT_*`。空字串視為未設定；completed status 預設 `Completed`，cache TTL 的無效或非正數值回退 3600 秒。production list route 同時設定 Nitro SWR 與 `public, s-maxage=<ttl>, stale-while-revalidate=<ttl>`。

Notion token/database id、status property 和 completed value 位於 private runtime config；public config 僅有 build date 與 commit SHA。build date 未指定時使用 Asia/Taipei 日期；commit SHA 依 Vercel、Showcase、GitHub 等變數依序 fallback。

`npm run check-env` 只輸出設定來源與各 key 是否存在，不輸出 secret value。執行時另可用 `/api/showcase/diagnostics` 檢查解析，或 `/api/showcase/health` 實際驗證 Notion 存取。

## 延伸閱讀

- [快速開始與導覽](../quickstart.md)
- [系統架構總覽](../architecture/system-overview.md)
- [Nuxt Showcase 使用體驗與資料快取](../frontend/showcase-experience.md)
