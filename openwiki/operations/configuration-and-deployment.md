---
type: operations-guide
title: 設定、執行與部署
description: 整理 Python 與 Nuxt 的環境設定、啟動指令、Docker topology、診斷與秘密管理。
tags: [operations, configuration, docker, deployment]
verified:
  - by: openwiki/0.4.3
    at: 2026-09-05T12:55:39.856Z
sources:
  - id: openwiki-source-6a7b8c07ba8513021d4c75f8
    resource: repo://.betterleaks.toml
  - id: openwiki-source-ee3ea3bd39689f7e4f5dc7c6
    resource: repo://.github/workflows/main.yml
  - id: openwiki-source-6d4b4e707b8d60b6ccfa3425
    resource: repo://.github/workflows/openwiki-update.yml
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
generated: { by: "codex", at: "2026-09-05T12:55:39.856Z" }
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

## Betterleaks 掃描設定

根目錄 `.betterleaks.toml` 宣告最低版本 `1.8.1`，並以 `[extend] useDefault = true` 延用預設規則。設定分成掃描前的路徑排除與 finding 的 placeholder 過濾。

`prefilter` 排除根目錄 `.env`、`.codex/auth.json`、`.codex/sessions`、`data/`、`frontend/nuxt-showcase/node_modules/`，以及根目錄的 `.venv`、`venv`、`env`、`__pycache__`、`.ruff_cache`、`.pytest_cache`。路徑模式允許開頭 `./`，但不是任意深度的同名目錄排除；例如 frontend `.env` 不在根目錄 `.env` 的排除式內。這些規則界定掃描涵蓋範圍，不代表被排除內容已通過秘密檢查。

`filter` 必須同時符合路徑與 secret 值條件才忽略 finding：

- `tests/`、Showcase `tests/` 與 `test-data/`、`.archive/tests/` 或 `.archive/test_` 開頭路徑，只忽略列出的 placeholder 模式：`secret`、`token`、`api-key`、`database-id`、`page-id`，`lock|openai|gemini|ollama` 搭配 `-secret` 或 `-key`，以及 `test|env|runtime|nuxt|mock` 加底線或連字號的限定字元字串。
- 根目錄與 Showcase 的 `.env.example` 僅忽略精確值 `example-maintainer-token`。

因此測試檔案仍屬掃描範圍，不符合上述值模式的 finding 不會由這份 filter 豁免。目前 `Makefile` 沒有 Betterleaks target，Python CI（`.github/workflows/main.yml`）執行 flake8 與 unittest，也沒有 Betterleaks step；存在設定檔不代表 CI 已自動執行掃描。

## OpenWiki 文件維護

`.github/workflows/openwiki-update.yml` 提供手動 `workflow_dispatch` 工作流程；目前沒有定時觸發器。它以完整 Git history checkout（`fetch-depth: 0`），讓 `openwiki code --update --print` 能和上次記錄的 commit 比對，而不會因 shallow clone 遺失更新基準。

Workflow 使用 Node.js 22，安裝固定版本的 OpenWiki 與可選 Mermaid 驗證依賴。執行時由 GitHub Secrets 注入 OpenAI 與 LangSmith connector credentials；設定檔只引用 secret 名稱，不應把實際值寫入 repository。LangSmith tracing credential 是選填，其 connector credential 則供 code-mode pull 使用。

更新完成後，`peter-evans/create-pull-request` 將 `openwiki/`、OpenWiki setup 文件與 workflow 變更收進 `openwiki/update` branch，建立 `docs: update OpenWiki` PR。Workflow 因此需要 `contents: write` 與 `pull-requests: write` 權限；產生的 wiki 頁面與 Claims 應透過 OpenWiki lifecycle 更新，不應直接手改 managed index、run metadata 或 Claims sidecar。

## 延伸閱讀

- [快速開始與開發導覽](../quickstart.md)
- [系統架構與端到端資料流](../architecture/system-overview.md)
- [模組邊界與外部依賴](../architecture/module-boundaries-and-dependencies.md)
- [HTTP API 與 Client 契約](../interfaces/http-api-and-clients.md)
- [LLM Providers、選擇與 Failover](../integrations/llm-providers.md)
- [Nuxt Showcase 使用體驗與資料快取](../frontend/showcase-experience.md)
