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
  - id: openwiki-source-269e1e25890c094aaa09d0a0
    resource: repo://.docker/Dockerfile
  - id: openwiki-source-bf5be0c9253ed1d07b502e10
    resource: repo://.githooks/pre-commit
  - id: openwiki-source-ee3ea3bd39689f7e4f5dc7c6
    resource: repo://.github/workflows/main.yml
  - id: openwiki-source-6d4b4e707b8d60b6ccfa3425
    resource: repo://.github/workflows/openwiki-update.yml
  - id: openwiki-source-dac0a79ee8362683638fa30e
    resource: repo://apps/showcase/nuxt.config.ts
  - id: openwiki-source-6b47ec2bb946dbfe3f605cea
    resource: repo://apps/showcase/README.md
  - id: openwiki-source-d2d7610281b3f0057b9f9314
    resource: repo://apps/showcase/scripts/check-env.mjs
  - id: openwiki-source-f987324e0612a557c62a85fb
    resource: repo://apps/showcase/server/api/showcase/results.get.ts
  - id: openwiki-source-98886cf9c4725ca201459fa1
    resource: repo://apps/showcase/server/plugins/showcase-error-cache.ts
  - id: openwiki-source-bae0c48de5dc6743f6dddd59
    resource: repo://apps/showcase/server/utils/config.ts
  - id: openwiki-source-3b0efe03f5b86982327fa144
    resource: repo://apps/showcase/server/utils/read-sync-config.ts
  - id: openwiki-source-51d27e8448c6ca65ff1ee504
    resource: repo://apps/showcase/server/utils/showcase-errors.ts
  - id: openwiki-source-4406f4d9096d90261e3f6198
    resource: repo://apps/whisper_summary/.env.example
  - id: openwiki-source-e8a3e4e8f72c5329a78957ec
    resource: repo://apps/whisper_summary/apps/api/schemas.py
  - id: openwiki-source-fb3a71308a5a59482c2767f3
    resource: repo://apps/whisper_summary/apps/workers/processing_worker.py
  - id: openwiki-source-445a1c8f48d3b2e4f898d6be
    resource: repo://apps/whisper_summary/core/config.py
  - id: openwiki-source-cd3c19edb3412c855091bcd0
    resource: repo://apps/whisper_summary/infrastructure/llm/model_options.py
  - id: openwiki-source-25d6d487d3ae6567d7b0397b
    resource: repo://apps/whisper_summary/infrastructure/llm/weighted_selection.py
  - id: openwiki-source-3224679c3e8a326edddf16ce
    resource: repo://apps/whisper_summary/infrastructure/notifications/discord.py
  - id: openwiki-source-44f784ddceb054f0c06a5950
    resource: repo://apps/whisper_summary/pyproject.toml
  - id: openwiki-source-5d30f93453a5fc9227aa0b47
    resource: repo://apps/whisper_summary/services/pipeline/processing_runner.py
  - id: openwiki-source-e201e686a785f09b6d899f0b
    resource: repo://compose.yaml
  - id: openwiki-source-012f2c78e3b1446dfc35803f
    resource: repo://Makefile
  - id: openwiki-source-da418bc01cba89686ece3492
    resource: repo://scripts/install-git-hooks.sh
generated: { by: "codex", at: "2026-10-10T15:06:52.784Z" }
verified:
  - by: openwiki/0.6.0
    at: 2026-10-10T15:06:52.784Z
---

# 設定、執行與部署

## Python 主系統

複製 `apps/whisper_summary/.env.example` 為 `apps/whisper_summary/.env` 並填入所需值，絕不可提交 secrets。`Config.validate()` 接受 `OPENAI_API_KEY`、`GOOGLE_GEMINI_API_KEY`、`OLLAMA_API_KEY` 任一值，或可在 PATH 找到的 Codex CLI；預設自動候選池只包含 Gemini 與 Codex CLI，因此僅有 OpenAI 或 Ollama key 仍無法從預設池選出模型。使用 Notion 時需同時提供 `NOTION_API_KEY` 與 `NOTION_DATABASE_ID`。Discord、Notion workspace URL、RSS 與維運 token 依功能選填。

`Config` 使用 `load_dotenv()` 載入可找到的 `.env`；Makefile 的 worker 入口另以 `--env-file apps/whisper_summary/.env` 指定設定來源。Config 固定 Asia/Taipei timezone，並確保 `data/`、`data/videos/`、`data/_summarized/` 存在。RSS 預設停用；poll interval、minimum interval 和 task API timeout 都至少為一秒。

`PROCESSING_ENGINE` 預設 `legacy`，也可設 `langgraph`；建立 task 時的 `processing_engine` 可逐筆覆寫。Worker 需要 `PROCESSING_WORKER_TOKEN`（若未設則沿用 `PROCESSING_LOCK_ADMIN_TOKEN`）才能透過中央 API claim、heartbeat 與回寫 task。`TASK_API_BASE_URL` 指向 API，`TASK_LOCK_TIMEOUT_SECONDS` 與 `TASK_LEASE_HEARTBEAT_SECONDS` 控制 lease 生命週期。常駐 worker 預設每 60 秒輪詢一次。Codex CLI 的執行檔與 timeout 可由 `CODEX_BIN`、`CODEX_TIMEOUT_SECONDS` 設定。

常用入口：

| 目的 | 指令 |
| --- | --- |
| 安裝 frozen Python dependencies | `uv sync --project apps/whisper_summary --frozen --no-install-project` |
| API | `make api` |
| Streamlit | `make streamlit` |
| SQLite worker 一次 | `make run` |
| Dedicated processing worker | `make processing-worker` |
| RSS monitor | `make rss-monitor` / `make rss-monitor-once` |
| 預覽過期 data 容量 | `make cleanup-data-dry-run` |
| 刪除過期 data | `make cleanup-data` |
| Python tests | `make test` |

`make install` 還會寫入 `/usr/local/bin/yt-dlp`，本機可能需要權限，不應把它視為純 dependency sync。API 的開發命令綁定 `0.0.0.0:8080` 並啟用 reload。

Docker Compose 以共用 runtime base、`apps/whisper_summary/.env` 與 bind-mounted repository 啟動 api、streamlit、processing-worker、rss-monitor。Dockerfile 以 `api`、`ui`、`worker` targets 分別安裝對應 dependency group。API 暴露 8080、Streamlit 暴露 8501；Streamlit、RSS monitor 與 processing worker 的 `TASK_API_BASE_URL` 都指向 Docker DNS 名稱 `api`。API 與 processing worker 啟動時預設更新 yt-dlp，可用 `YTDLP_AUTO_UPDATE=0` 停用。

processing lock 管理端點需 `PROCESSING_LOCK_ADMIN_TOKEN`。`make clear-processing-lock` 會從 environment 或 `apps/whisper_summary/.env` 取 token 並送出 force release；執行前應先用 GET/dry-run 確認目標 backend 與 lock age，避免中斷活躍 worker。

### Discord 知識庫連結設定

`DISCORD_WEBHOOK_URL` 控制是否傳送完成通知。選填 `SHOWCASE_BASE_URL` 可讓訊息附上摘要詳細頁，設定於實際執行 processing pipeline 的環境：

```dotenv
SHOWCASE_BASE_URL=https://knowledge.example.com
```

填網站根網址，不包含 `/results`；預設未設定，不會自動連到任何特定部署。通知使用摘要的 `notion_page_id`，清除根網址前後空白與尾端斜線，將合法 UUID 正規化後產生 `/results/{id}`。只接受有 host 的 HTTP/HTTPS URL；內嵌帳密、query、fragment、空白或無效 port 會讓新連結被略過。缺少或無效摘要 ID（包括測試模式的模擬 ID）也只略過知識庫連結。

通知保留完成標題與 YouTube 網址，僅選擇性附加知識庫摘要入口，不再附加 Notion 網址；知識庫連結不要求 `NOTION_URL`。Discord request 仍有 10 秒預設 timeout；HTTP 錯誤或 request exception 會記錄並回傳 `False`。

設定變更後重新載入執行摘要的 process。Compose 的 services 共用 env_file，需重新建立 container 才載入更新值，例如 `docker compose up -d --force-recreate processing-worker`；單純 restart 不會重新載入 env_file。清空新設定並重新載入環境即可讓通知只顯示完成標題與影片網址。部署網址保留在不受 Git 追蹤的 `.env` 或環境變數，測試與文件僅使用測試網域。

### 本機 Data 清理

`make cleanup-data-dry-run` 只統計符合條件的檔案數與預估可釋放容量，不列出或刪除檔案；確認後才執行 `make cleanup-data`。實際清理會顯示 `data/videos` 與 `data/summaries` 的清理前容量、清理後容量與總 reclaimed 容量。

影片與 summary artifacts 預設都保留 3 天；可在命令列以 `VIDEO_RETENTION_DAYS` 與 `SUMMARY_RETENTION_DAYS` 覆寫，例如 `make cleanup-data-dry-run VIDEO_RETENTION_DAYS=30 SUMMARY_RETENTION_DAYS=365`。兩個值都必須是非負整數，且 `data/videos` 與 `data/summaries` 都必須存在，否則 target 會在掃描或刪除前停止。`readme.md` 也記載了 3 天預設值，並建議先用 dry-run 預覽。

清理範圍只包含 `data/videos` 與 `data/summaries` 中超過期限的 regular files，不會處理 `data/tasks.db` 或其他 `data` 內容。這兩個 Make targets 都是人工觸發的維運操作；目前沒有自動排程，也不會在 worker 完成後自動執行。

## Nuxt Showcase

在 `apps/showcase` 執行 `npm install`、`npm run dev`、`npm run test`、`npm run build`。`make showcase` 載入 `apps/showcase/.env`（若存在）。

Showcase 設定優先序為 runtime config，其次標準 `NOTION_*`/`SHOWCASE_*`，最後相容用的 `NUXT_*`。空字串視為未設定；completed status 預設 `Completed`，cache TTL 的無效或非正數值回退 3600 秒。production list route 保留同一 TTL 的 Nitro SWR，但 route rule 不再設定固定 Cache-Control header；列表與詳情 handler 仍產生成功回應的 public s-maxage／stale-while-revalidate 標頭，避免固定規則覆蓋錯誤的 no-store。

Notion token/database id、status property、completed value，以及選用同步的 Upstash token、個人同步碼與 session secret 位於 private runtime config；public config 僅包含公開的 site URL、build date 與 commit SHA。build date 未指定時使用 Asia/Taipei 日期；commit SHA 依 Vercel、Showcase、GitHub 等變數依序 fallback。

跨裝置已讀同步需同時設定 `READ_STATE_SYNC_ENABLED`、`UPSTASH_REDIS_REST_URL`、`UPSTASH_REDIS_REST_TOKEN`、`READ_STATE_SYNC_ACCESS_TOKEN` 和 `READ_STATE_SYNC_SESSION_SECRET`；`READ_STATE_SYNC_SPACE_ID` 預設 `personal`。設定細節與本機降級行為見[跨裝置已讀同步](../frontend/read-state-sync.md)。

`npm run check-env` 輸出設定來源、key 是否存在，以及 completed status 和 cache TTL 的解析字串，不輸出 Notion secret value。它讀取 `apps/showcase/.env`，且不覆寫既有 process environment；`make showcase` 則會 export 該檔案的值。check-env 是獨立程序，執行成功不會把讀到的環境傳給後續 `npm run dev`。公開 diagnostics 與 health API 已移除；check-env 也不能證明已部署 runtimeConfig 正確或 Notion 權限可用。部署後請透過平台設定與 server log 排錯。

Showcase 對每次 Notion HTTP 請求設定固定 5 秒 timeout，包含 schema、query、page 與每次 blocks 分頁／子內容讀取；整篇文章的累計時間仍可能超過 5 秒。後端不自動重試；已有成功快取時保留舊資料，沒有快取時回傳 502，後續請求可重新嘗試。詳細頁的三種初始讀取會平行開始，見[Notion 資料整合](../integrations/notion-and-showcase.md)。

週報內容的整理、私人 checkpoint 與 registry 建置見[每週回顧整理與內容發布流程](../workflows/weekly-insights.md)；Streamlit 的直接 repository 存取與操作歷史見[Streamlit 任務操作與狀態導覽](../frontend/streamlit-console.md)。

## Betterleaks 掃描設定

根目錄 `.betterleaks.toml` 宣告最低版本 `1.8.1`，並以 `[extend] useDefault = true` 延用預設規則。設定分成一般目錄掃描前的路徑排除與 finding 的 placeholder 過濾。

一般掃描的 `prefilter` 排除 `.git`、`data/`、Showcase 的 dependency/build/coverage 產物，以及根目錄的 Python virtual environments 與 caches；它刻意不排除 `.env` 或 Codex auth/session，因此 `betterleaks dir .` 仍可能報告未追蹤的本機 credential。`dir` 檢查 working tree，不是日常確認 Git commit 內容的入口。

`filter` 必須同時符合路徑與 secret 值條件才忽略 finding：

- `apps/whisper_summary/tests/`、Showcase `tests/` 與 `test-data/`、`.archive/tests/` 或 `.archive/test_` 開頭路徑，只忽略列出的 placeholder 模式：`secret`、`token`、`api-key`、`database-id`、`page-id`，`lock|openai|gemini|ollama` 搭配 `-secret` 或 `-key`，以及 `test|env|runtime|nuxt|mock` 加底線或連字號的限定字元字串。
- Python app 與 Showcase 的 `.env.example` 僅忽略精確值 `example-maintainer-token`。

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

### Showcase 安全錯誤與 log

必要設定缺少時回固定 500 訊息，上游讀取失敗且無快取時回固定 502 訊息，不包含 env snapshot 或 Notion error body。server log 的 configuration unavailable 只記錄缺少設定名稱或布林值；Notion query failed 只記錄 results／detail 與 timeout、network-or-type-error、upstream-error 等預定義分類，包含背景更新失敗，不輸出原始 Error 或 secrets。

Nitro error hook 對展示列表、詳情與每週洞察頁面/API 的 4xx、5xx 錯誤補上 Cache-Control: no-store，防止 SWR 代理回應遺失 handler 標頭；成功回應與其他 API 不套用這項規則。每週洞察成功內容由 repository 週報文件建置，不需要額外 runtime secret。
