---
type: operations-guide
title: 設定、執行與部署
description: 整理 Python 與 Nuxt 的環境設定、啟動指令、Docker topology、診斷與秘密管理。
tags: [operations, configuration, docker, deployment]
sources:
  - id: openwiki-source-6b7ed5378873fbdfb150c3d7
    resource: repo://.betterleaks-pre-commit.toml
  - id: openwiki-source-6a7b8c07ba8513021d4c75f8
    resource: repo://.betterleaks.toml
  - id: openwiki-source-bf5be0c9253ed1d07b502e10
    resource: repo://.githooks/pre-commit
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
  - id: openwiki-source-da418bc01cba89686ece3492
    resource: repo://scripts/install-git-hooks.sh
  - id: openwiki-source-526d4ed1a7d9ebdeb9c244a6
    resource: repo://src/core/config.py
  - id: openwiki-source-36d48d46c256392dc902bc2d
    resource: repo://src/infrastructure/llm/model_options.py
  - id: openwiki-source-791a1bcc2cae6ed2d067dedb
    resource: repo://src/infrastructure/llm/weighted_selection.py
  - id: openwiki-source-df04114da62d5e054970a89f
    resource: repo://src/services/pipeline/processing_runner.py
generated: { by: "codex", at: "2026-09-05T14:47:18.852Z" }
verified:
  - by: openwiki/0.4.3
    at: 2026-09-05T14:47:18.852Z
---

# 設定、執行與部署

## Python 主系統

複製 `.env.example` 為 `.env` 並填入所需值，絕不可提交 secrets。`Config.validate()` 接受 `OPENAI_API_KEY`、`GOOGLE_GEMINI_API_KEY` 或 `OLLAMA_API_KEY` 任一值，但預設 worker 使用的自動候選池目前只有 Gemini，因此直接使用預設流程需設定 `GOOGLE_GEMINI_API_KEY`；僅有 OpenAI 或 Ollama key 不會自動新增候選模型。使用 Notion 時需同時提供 `NOTION_API_KEY` 與 `NOTION_DATABASE_ID`。Discord、Notion workspace URL、RSS 與 lock admin token 依功能選填。

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

Docker Compose 以同一 image、`.env` 與 bind-mounted repository 啟動 api、streamlit、rss-monitor。API 暴露 8080、Streamlit 暴露 8501；後兩者的 `TASK_API_BASE_URL` 指向 Docker DNS 名稱 `api`。API 啟動時預設更新 yt-dlp，可在 Compose 載入的 `.env` 設定 `YTDLP_AUTO_UPDATE=0` 停用；僅在主機 shell 設定此值，不會由目前的 Compose 設定自動傳入 container。

processing lock 管理端點需 `PROCESSING_LOCK_ADMIN_TOKEN`。`make clear-processing-lock` 會從 environment 或 root `.env` 取 token 並送出 force release；執行前應先用 GET/dry-run 確認目標 backend 與 lock age，避免中斷活躍 worker。

## Nuxt Showcase

在 `frontend/nuxt-showcase` 執行 `npm install`、`npm run dev`、`npm run test`、`npm run build`。`make showcase` 優先載入 frontend `.env`，不存在才使用 repository root `.env`。

Showcase 設定優先序為 runtime config，其次標準 `NOTION_*`/`SHOWCASE_*`，最後相容用的 `NUXT_*`。空字串視為未設定；completed status 預設 `Completed`，cache TTL 的無效或非正數值回退 3600 秒。production list route 同時設定 Nitro SWR 與 `public, s-maxage=<ttl>, stale-while-revalidate=<ttl>`。

Notion token/database id、status property 和 completed value 位於 private runtime config；public config 僅有 build date 與 commit SHA。build date 未指定時使用 Asia/Taipei 日期；commit SHA 依 Vercel、Showcase、GitHub 等變數依序 fallback。

`npm run check-env` 輸出設定來源、key 是否存在，以及 completed status 和 cache TTL 的解析字串，不輸出 Notion secret value。它優先讀 frontend `.env`，不存在才讀 root `.env`，且不覆寫既有 process environment；`make showcase` 則會 export 選定檔案的值。check-env 是獨立程序，執行成功不會把讀到的環境傳給後續 `npm run dev`；若依賴 root `.env`，請從 repository root 使用 `make showcase`。執行時另可用 `/api/showcase/diagnostics` 檢查解析，或 `/api/showcase/health` 實際驗證 Notion 存取。

## Betterleaks 掃描設定

根目錄 `.betterleaks.toml` 宣告最低版本 `1.8.1`，並以 `[extend] useDefault = true` 延用預設規則。設定分成一般目錄掃描前的路徑排除與 finding 的 placeholder 過濾。

一般掃描的 `prefilter` 排除 `.git`、`data/`、Showcase 的 dependency/build/coverage 產物，以及根目錄的 Python virtual environments 與 caches；它刻意不排除 `.env` 或 Codex auth/session，因此 `betterleaks dir .` 仍可能報告未追蹤的本機 credential。`dir` 檢查 working tree，不是日常確認 Git commit 內容的入口。

`filter` 必須同時符合路徑與 secret 值條件才忽略 finding：

- `tests/`、Showcase `tests/` 與 `test-data/`、`.archive/tests/` 或 `.archive/test_` 開頭路徑，只忽略列出的 placeholder 模式：`secret`、`token`、`api-key`、`database-id`、`page-id`，`lock|openai|gemini|ollama` 搭配 `-secret` 或 `-key`，以及 `test|env|runtime|nuxt|mock` 加底線或連字號的限定字元字串。
- 根目錄與 Showcase 的 `.env.example` 僅忽略精確值 `example-maintainer-token`。

因此測試檔案仍屬掃描範圍，不符合上述值模式的 finding 不會由這份 filter 豁免。

日常 Git 防護使用 `.betterleaks-pre-commit.toml`。它繼承相同 finding filter，但以 `prefilter = false` 覆寫一般掃描的路徑排除，讓 `betterleaks git --staged` 檢查所有 Git index paths，包括以 `git add -f` 強制加入的 ignored 檔案。Hook 全程 redact，Betterleaks executable 或設定檔不存在時會拒絕 commit。

執行 `make install-hooks` 會設定 repository-local `core.hooksPath=.githooks`；若 checkout 已指向其他 hooks path，安裝腳本會停止並要求人工合併，不會覆寫。可用 `make betterleaks-staged` 手動執行同一檢查。Git hook 不會隨 clone 自動啟用，每個 checkout 都需安裝一次。Python CI（`.github/workflows/main.yml`）仍只執行 flake8 與 unittest，沒有 Betterleaks step；本機 hook 不等同 server-side CI gate。

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
