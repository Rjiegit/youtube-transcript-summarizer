# YouTube 影片轉錄與摘要平台

這個專案會接收 YouTube URL，使用 `yt-dlp` 下載媒體、以 faster-whisper 轉錄，再透過 LLM 產生繁體中文摘要。任務與結果可儲存在 SQLite、Markdown 與 Notion，並提供 Streamlit、FastAPI、RSS monitor、Browser Extension 與 Nuxt Showcase 等入口。

Discord 完成通知可附上 Showcase 摘要入口，設定方式見 [通知操作手冊](docs/operations/notifications.md)。

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

### Processing engine 與 Worker

支援 Legacy 與 LangGraph engine，以及本機／Docker 多 Worker。切換、啟動與故障處置見 [Processing 操作手冊](docs/operations/processing.md)。

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

## 主要元件

Python 處理平台、Browser Extension 與 Nuxt Showcase 的責任與依賴，見 [系統架構](openwiki/architecture/system-overview.md)及 [模組邊界](openwiki/architecture/module-boundaries-and-dependencies.md)。

## 文件怎麼讀

- [操作文件導覽](docs/README.md)：人工維護的安裝、設定、維運與內容規則。
- [OpenWiki](openwiki/quickstart.md)：從程式與測試整理的架構、資料流與內部機制。
- [CONTRIBUTING.md](CONTRIBUTING.md)、[AGENTS.md](AGENTS.md)：開發與協作規則。

操作步驟只在 docs 維護，README 提供摘要與入口；實際行為仍以原始碼與測試為準。

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

- [Nuxt Showcase README](apps/showcase/README.md)：Nuxt 啟動、必要設定與功能文件入口。
- [Browser Extension README](apps/browser-extension/README.md)：本機載入、整合邊界與驗證方式。
- [Browser Extension 架構文件](openwiki/integrations/browser-extension.md)：Extension API 設定與安全邊界；OpenWiki 下次更新時會同步新路徑。

### 成功任務的媒體清理

成功任務預設清理媒體；保留開關、共用資料限制與手動清理見 [媒體清理操作手冊](docs/operations/media-cleanup.md)。

### 雲端影片收件匣

Showcase 可受保護提交 YouTube 網址，Supabase Queue 暫存，本機上線後執行
`make video-inbox-bridge` 透過本機 Task API 入庫，再由既有 processing-worker 處理。
安裝 migration、權限與設定請見 [影片收件匣文件](docs/video-inbox.md)。
