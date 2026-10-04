# YouTube 影片轉錄與摘要平台

這個專案會接收 YouTube URL，使用 `yt-dlp` 下載媒體、以 faster-whisper 轉錄，再透過 LLM 產生繁體中文摘要。任務與結果可儲存在 SQLite、Markdown 與 Notion，並提供 Streamlit、FastAPI、RSS monitor、Browser Extension 與 Nuxt Showcase 等入口。

若要讓 Discord 完成通知附上知識庫摘要連結，在執行摘要流程的
`apps/whisper_summary/.env` 設定 `SHOWCASE_BASE_URL=https://knowledge.example.com`，
並重新載入 worker 環境。通知會使用摘要的 Notion page ID 連往 `/results/{id}`；
未設定時保留原有通知。Compose 的 env_file 變更需重新建立 worker container。

## 系統流程

```text
Streamlit / Extension / RSS monitor / HTTP client
                       │
                       ▼
                    FastAPI
                       │
                       ▼
             SQLite / Notion task backend
                       │
                       ▼
                ProcessingWorker
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   Legacy engine             LangGraph engine
          └────────────┬────────────┘
        yt-dlp → faster-whisper → LLM
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Markdown      Notion       Discord
                       │
                       ▼
                 Nuxt Showcase
```

CLI worker 可以直接處理 backend 中的待辦任務；Nuxt Showcase 則直接讀取 Notion 的完成結果，不會呼叫 Python Task API。

### Processing engine 切換

processing pipeline 支援兩個具有相同外部行為的 orchestration engine：

- `legacy`：既有循序流程，也是未設定時的安全預設。
- `langgraph`：以 LangGraph `StateGraph` 執行相同的下載、轉錄、摘要、儲存與通知步驟。

在 `apps/whisper_summary/.env` 設定全域預設，變更後重啟 processing worker：

```bash
PROCESSING_ENGINE=legacy
# 驗證完成後可改為：PROCESSING_ENGINE=langgraph
```

Streamlit 建立任務時也可選擇 `Legacy` 或 `LangGraph` 覆寫單筆任務；選擇
`Follow system default` 則使用 worker 的環境變數。API client 可在 `POST /tasks`
加入 `"processing_engine": "legacy"` 或 `"langgraph"`。回退時將環境變數改回
`legacy` 即可，已明確指定 engine 的待處理任務仍以任務設定優先。

SQLite 會自動新增 `processing_engine` 欄位。若 Notion task backend 需要使用單筆
覆寫，請先在 task database 建立名為 `Processing Engine` 的 Select property，選項為
`Legacy` 與 `LangGraph`；未設定單筆覆寫的既有頁面仍使用全域預設。

## 快速開始

需求：Python 3.14、[`uv`](https://docs.astral.sh/uv/)、`yt-dlp`，以及至少一組可供目前自動候選池使用的 LLM credential。完整設定條件請參考 [OpenWiki 快速開始](openwiki/quickstart.md)。

```bash
cp apps/whisper_summary/.env.example apps/whisper_summary/.env
uv sync --project apps/whisper_summary --frozen --no-install-project
make install-hooks
make api
```

Python 專案設定、lockfile 與 `.env` 位於 `apps/whisper_summary/`。`make` 指令會指定 uv project，
並把 `apps/` 加入 `PYTHONPATH`；直接執行 Python 模組或 unittest 時，需使用
`uv run --project apps/whisper_summary` 與 `PYTHONPATH=apps`。
Python 測試位於 `apps/whisper_summary/tests/`，Showcase 測試位於 `apps/showcase/tests/`；
兩邊共用的 Notion 契約 fixture 位於 `contracts/`。

另開 terminal 啟動 Streamlit：

```bash
make streamlit
```

預設服務：

- FastAPI：<http://localhost:8080>
- FastAPI Swagger UI：<http://localhost:8080/docs>
- Streamlit：<http://localhost:8501>

本機尚未安裝 `yt-dlp` 時，可執行：

```bash
make yt-dlp-update
```

這會寫入 `/usr/local/bin/yt-dlp`，部分環境可能需要額外權限。

## Docker

```bash
docker compose up -d
```

預設啟動：

- `api`：Task API
- `streamlit`：主要操作介面
- `processing-worker`：透過 API claim task lease，並執行 processing pipeline
- `rss-monitor`：RSS polling process；需設定 `RSS_MONITOR_ENABLED=true` 才會輪詢

Nuxt Showcase 不在此 Compose topology 中。

## 常用操作

```bash
# 下載 YouTube 媒體
make yt-dlp url="<YOUTUBE_URL>"

# 處理 SQLite queue
make run
make processing-worker

# 下載後立即處理
make auto url="<YOUTUBE_URL>"

# RSS monitor
make rss-monitor
make rss-monitor-once

# 查詢 Gemini 可用模型（需要 GOOGLE_GEMINI_API_KEY）
make list-models

# Python 測試與 lint
make test
make test-unit
make test-integration
make lint

# Showcase 測試與 build
npm --prefix apps/showcase run test
npm --prefix apps/showcase run build

# Browser Extension manifest、asset 與 JavaScript validation
make extension-check
```

`make cleanup-data` 預設清理超過 3 天的影片與摘要檔案；可先執行 `make cleanup-data-dry-run` 預覽。
完整的啟動、環境變數、資料清理與部署說明請看 [設定、執行與部署](openwiki/operations/configuration-and-deployment.md)。

## 多 Worker 模式

Processing API 是 task lease 的中央協調者。Docker 與本機 worker 可以同時運行；每個
worker 一次處理一筆任務，而同一筆任務只會由一個 lease owner 取得。

先在 `apps/whisper_summary/.env` 設定 worker token（未設定時暫時相容
`PROCESSING_LOCK_ADMIN_TOKEN`）：

```env
PROCESSING_WORKER_TOKEN=<random-secret>
```

Docker worker 使用 Compose 內部 API URL：

```bash
docker compose up -d api streamlit rss-monitor processing-worker
```

本機 worker 使用 `TASK_API_BASE_URL`（預設 `http://localhost:8080`），並能使用主機上的
Codex CLI：

```bash
make processing-worker
```

兩者會以唯一 instance ID 競爭任務。Worker 以 heartbeat 維持 lease；lease 過期時任務
會直接標記為 `Failed`，不會自動交給另一個 worker 重跑。確認舊 worker 已停止後，可透過
既有 retry 操作建立新任務。Streamlit 的 `Processing Leases` 維運區可查看及手動標記
active lease 為 Failed。

## 主要元件

| 元件 | 責任 |
| --- | --- |
| `apps/whisper_summary/apps/api/main.py` | FastAPI app 建立與 feature router 註冊 |
| `apps/whisper_summary/apps/api/routers/` | Task、RSS 與 processing lock endpoints |
| `apps/whisper_summary/apps/api/schemas.py` | API request／response models |
| `apps/whisper_summary/domain/ports/` | Application services 使用的 repository contracts |
| `apps/whisper_summary/infrastructure/composition.py` | Processing pipeline 的 concrete adapter 組裝 |
| `apps/whisper_summary/infrastructure/repository_composition.py` | Database 與 RSS repository 組裝 |
| `apps/whisper_summary/apps/ui/streamlit_app.py` | Streamlit UI 入口 |
| `apps/whisper_summary/apps/workers/cli.py` | 同步處理 queue 的 CLI worker |
| `apps/whisper_summary/apps/workers/processing_worker.py` | 持續輪詢 queue 的 dedicated processing worker |
| `apps/whisper_summary/apps/workers/rss_monitor.py` | YouTube channel RSS monitor |
| `apps/whisper_summary/services/pipeline/processing_runner.py` | Queue、lock 與 processing engine 選擇 |
| `apps/whisper_summary/services/pipeline/engines.py` | 共用 pipeline operations、legacy engine 與 engine contract |
| `apps/whisper_summary/services/pipeline/langgraph_engine.py` | LangGraph `StateGraph` orchestration |
| `apps/whisper_summary/infrastructure/media/` | `yt-dlp` 下載與 faster-whisper 轉錄 |
| `apps/whisper_summary/infrastructure/llm/` | LLM provider、候選模型與 failover |
| `apps/whisper_summary/infrastructure/persistence/` | SQLite 與 Notion adapters |
| `apps/browser-extension/` | Chrome／Edge Manifest V3 client |
| `apps/showcase/` | 從 Notion 讀取成果的 Nuxt 展示站 |

## 文件怎麼讀

文件權威順序：

1. 原始碼與測試：實際行為。
2. `openwiki/`：目前架構、流程、整合與維運說明。
3. `CONTRIBUTING.md`、`AGENTS.md`：人類與 AI 開發規則。
4. `.docs/`：仍需保留但尚未整併的補充設計資料；目前行為仍以程式碼、測試與 OpenWiki 為準。

建議的新手閱讀順序：

1. [快速開始與開發導覽](openwiki/quickstart.md)
2. [系統架構與端到端資料流](openwiki/architecture/system-overview.md)
3. [任務生命週期與併發控制](openwiki/workflows/task-lifecycle.md)
4. [媒體轉錄與摘要流程](openwiki/workflows/media-processing.md)

若已知道要修改的範圍，可直接使用 [Quickstart 的任務導覽](openwiki/quickstart.md#依任務找文件)。

## 開發與安全

開始修改前請閱讀 [CONTRIBUTING.md](CONTRIBUTING.md)。重要原則如下：

- 不要提交 `apps/whisper_summary/.env`、API key 或其他 secrets。
- 大型下載與產物放在 `data/`，不要提交到 Git。
- Python 測試使用 `unittest`；外部 API、Notion、LLM 與網路操作應使用 mock 或 fake。
- 提交前至少執行與變更範圍相符的測試、`make lint`，並確認 staged secret scan。
- 新增執行入口時，同步更新 README 與 Makefile target。

## 子專案

- [Nuxt Showcase README](apps/showcase/README.md)：Nuxt 開發、環境變數、cache 與 diagnostics。
- [Browser Extension README](apps/browser-extension/README.md)：本機載入、整合邊界與驗證方式。
- [Browser Extension 架構文件](openwiki/integrations/browser-extension.md)：Extension API 設定與安全邊界；OpenWiki 下次更新時會同步新路徑。
