# YouTube 影片轉錄與摘要平台

這個專案會接收 YouTube URL，使用 `yt-dlp` 下載媒體、以 faster-whisper 轉錄，再透過 LLM 產生繁體中文摘要。任務與結果可儲存在 SQLite、Markdown 與 Notion，並提供 Streamlit、FastAPI、RSS monitor、Browser Extension 與 Nuxt Showcase 等入口。

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

## 快速開始

需求：Python 3.14、[`uv`](https://docs.astral.sh/uv/)、`yt-dlp`，以及至少一組可供目前自動候選池使用的 LLM credential。完整設定條件請參考 [OpenWiki 快速開始](openwiki/quickstart.md)。

```bash
cp .env.example .env
uv sync --frozen --no-install-project
make install-hooks
make api
```

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

- `api`：Task API 與 background processing
- `streamlit`：主要操作介面
- `rss-monitor`：RSS polling process；需設定 `RSS_MONITOR_ENABLED=true` 才會輪詢

Nuxt Showcase 不在此 Compose topology 中。

## 常用操作

```bash
# 下載 YouTube 媒體
make yt-dlp url="<YOUTUBE_URL>"

# 處理 SQLite queue
make run

# 下載後立即處理
make auto url="<YOUTUBE_URL>"

# RSS monitor
make rss-monitor
make rss-monitor-once

# Python 測試與 lint
make test
uv run flake8 .

# Showcase 測試與 build
npm --prefix frontend/nuxt-showcase run test
npm --prefix frontend/nuxt-showcase run build
```

完整的啟動、環境變數、資料清理與部署說明請看 [設定、執行與部署](openwiki/operations/configuration-and-deployment.md)。

## 主要元件

| 元件 | 責任 |
| --- | --- |
| `src/apps/api/main.py` | FastAPI task、retry、RSS 與 processing lock endpoints |
| `src/apps/ui/streamlit_app.py` | Streamlit UI 入口 |
| `src/apps/workers/cli.py` | 同步處理 queue 的 CLI worker |
| `src/apps/workers/rss_monitor.py` | YouTube channel RSS monitor |
| `src/services/pipeline/processing_runner.py` | 下載、轉錄、摘要、儲存與通知的 orchestration |
| `src/infrastructure/media/` | `yt-dlp` 下載與 faster-whisper 轉錄 |
| `src/infrastructure/llm/` | LLM provider、候選模型與 failover |
| `src/infrastructure/persistence/` | SQLite 與 Notion adapters |
| `apps/browser-extension/` | Chrome／Edge Manifest V3 client |
| `frontend/nuxt-showcase/` | 從 Notion 讀取成果的 Nuxt 展示站 |

## 文件怎麼讀

文件權威順序：

1. 原始碼與測試：實際行為。
2. `openwiki/`：目前架構、流程、整合與維運說明。
3. `CONTRIBUTING.md`、`AGENTS.md`：人類與 AI 開發規則。
4. `openspec/`：功能規格、提案與決策歷史。
5. `.docs/`：仍需保留但尚未整併的補充設計資料；目前行為仍以程式碼、測試與 OpenWiki 為準。

建議的新手閱讀順序：

1. [快速開始與開發導覽](openwiki/quickstart.md)
2. [系統架構與端到端資料流](openwiki/architecture/system-overview.md)
3. [任務生命週期與併發控制](openwiki/workflows/task-lifecycle.md)
4. [媒體轉錄與摘要流程](openwiki/workflows/media-processing.md)

若已知道要修改的範圍，可直接使用 [Quickstart 的任務導覽](openwiki/quickstart.md#依任務找文件)。

## 開發與安全

開始修改前請閱讀 [CONTRIBUTING.md](CONTRIBUTING.md)。重要原則如下：

- 不要提交 `.env`、API key 或其他 secrets。
- 大型下載與產物放在 `data/`，不要提交到 Git。
- Python 測試使用 `unittest`；外部 API、Notion、LLM 與網路操作應使用 mock 或 fake。
- 提交前至少執行與變更範圍相符的測試、`uv run flake8 .`，並確認 staged secret scan。
- 新增執行入口時，同步更新 README 與 Makefile target。

## 子專案

- [Nuxt Showcase README](frontend/nuxt-showcase/README.md)：Nuxt 開發、環境變數、cache 與 diagnostics。
- [Browser Extension README](apps/browser-extension/README.md)：本機載入、整合邊界與驗證方式。
- [Browser Extension 架構文件](openwiki/integrations/browser-extension.md)：Extension API 設定與安全邊界；OpenWiki 下次更新時會同步新路徑。
- [OpenSpec](openspec/project.md)：規格與變更提案入口。
