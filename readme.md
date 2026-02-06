# YouTube 影片文字轉錄與摘要工具

此專案是一個專為內容創作者、研究人員和學習者設計的 YouTube 影片文字轉錄與摘要工具。它能自動下載 YouTube 影片、提取音訊、進行高精度語音轉文字，並利用先進的大型語言模型（LLM）生成結構化摘要，幫助用戶快速理解和提取影片中的關鍵信息。

## 專案架構與工作流程

本工具採用模組化設計，並將核心程式碼集中在 `src/` 目錄：

- **`src/infrastructure/media/transcription/transcriber.py`**：使用 Whisper/Faster-Whisper 進行音訊轉錄。
- **`src/infrastructure/llm/summarizer_service.py`**：整合 OpenAI / Gemini / Mock 後端以生成摘要。
- **`src/apps/api/main.py`**：FastAPI 入口，提供 `/tasks`、`/processing-jobs`、`/processing-lock` 等端點。
- **`src/apps/ui/streamlit_app.py`**：Streamlit UI。
- **`src/infrastructure/media/downloader.py`**：以 yt-dlp 管理影片與音訊下載。
- **`src/services/pipeline/processing_runner.py`**：`ProcessingWorker` orchestration，負責任務鎖、轉錄、摘要與儲存。
- **`src/infrastructure/storage/file_storage.py`**：負責 Markdown 檔案輸出及檔名清理。
- **`src/infrastructure/storage/summary_storage.py`**：將摘要同步到 Notion；可依需求替換其他儲存後端。
- **`src/apps/workers/cli.py`**：CLI/排程入口，方便 `make run` 與 Docker scheduler 呼叫。

> 註：請直接 import `src.*` 內的模組，實際邏輯皆位於 `src/`。

工作流程自動化且高效：從 YouTube 下載影片 → 提取音訊 → 使用 Whisper 進行轉錄 → 使用 LLM 生成摘要 → 以 Markdown 格式保存結果 → 可選擇存儲到 Notion。整個流程在 Docker 容器中運行，確保環境一致性與易於部署。

## 技術特色

- **高精度轉錄**: 使用 OpenAI 的 Whisper 模型，支持多種語言的高質量語音轉文字
- **智能摘要**: 利用先進的 LLM 技術，生成結構化、易於理解的內容摘要
- **靈活配置**: 支持多種 LLM 選項，包括雲端服務 (OpenAI、Google) 和本地部署 (Ollama)
- **容器化部署**: 使用 Docker 確保環境一致性，簡化安裝和配置過程
- **中文優化**: 專為中文內容設計，輸出格式和提示詞均已優化

## 功能特點

- 使用 OpenAI 的 Whisper 模型進行高精度語音轉文字
- 支援多種 LLM 進行摘要生成：Google Gemini、OpenAI GPT、Ollama (本地模型)
- 自動處理 YouTube 影片下載、轉錄與摘要的完整工作流程
- 以 Markdown 格式輸出結構化摘要
- Docker 容器化部署，確保環境一致性

## 環境需求

- Docker 與 Docker Compose
- （若不使用 Docker）Python 3.11 + `uv`
- 以下至少需要一個 API Key 或服務：
  - OpenAI API Key (可選)
  - Google Gemini API Key (可選)
  - Ollama 本地服務 (可選)

## 快速開始

### 1. 設置環境

1. 克隆此專案到本地：

```bash
git clone <repository-url>
cd <repository-directory>
```

2. 創建 `.env` 檔案並設置 API Key (至少選擇一個)：

```
# OpenAI API (可選)
OPENAI_API_KEY=your_openai_api_key

# Google Gemini API (可選)
GOOGLE_GEMINI_API_KEY=your_gemini_api_key

> 註：Gemini 摘要模型目前採「加權隨機」挑選以降低單一模型遇到 rate limit 的機率；可在 `src/infrastructure/llm/model_options.py` 調整 `GEMINI_WEIGHTED_MODELS`（model/weight）。

# Notion 儲存與通知（可選）
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_notion_database_id
NOTION_URL=https://www.notion.so/your-workspace

# Discord 通知（可選）
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/......

# Processing lock 管理
PROCESSING_LOCK_ADMIN_TOKEN=your_admin_token
```

### 2. 啟動 Docker 服務

在專案根目錄執行：

```bash
docker compose up -d
```

此指令會啟動 Docker Compose 服務。
- 預設對外開放 8501（Streamlit）與 8080（FastAPI）。
- `api` 服務啟動時會自動更新 `yt-dlp`（可用 `YTDLP_AUTO_UPDATE=0` 關閉）。

此指令會啟動兩個服務：
- `streamlit`：Streamlit UI（8501）
- `api`：FastAPI（8080）

### 3. 進入服務容器

- 進入 Streamlit 容器：

  ```bash
  docker compose exec streamlit bash
  ```

- 進入 API 容器：

  ```bash
  docker compose exec api bash
  ```

### 4. 安裝依賴

進入任一服務容器後，安裝所需的依賴項：

```bash
make install
```

此指令會：
- 下載並安裝最新版本的 yt-dlp 到 /usr/local/bin/
- 設置 yt-dlp 的執行權限
- 以 `uv` 同步並安裝 Python 依賴（`uv sync --frozen`）

## 使用方法

### 下載 YouTube 影片

使用以下指令下載 YouTube 影片的音訊到 `data/videos/` 目錄：

```bash
make yt-dlp url="YOUR_YOUTUBE_URL"
```

### 執行文字轉錄與摘要

處理 `data/videos/` 目錄下的所有音訊檔案：

```bash
make run
```
或直接呼叫 CLI 入口：
```bash
uv run python -m src.apps.workers.cli --db-type sqlite --worker-id local-run
```
（`--db-type notion` 亦支援，適合 Notion 佇列；`--worker-id` 可選，用於鎖狀態追蹤。）

### 一鍵完成整個流程

下載影片並立即進行處理：

```bash
make auto url="YOUR_YOUTUBE_URL"
```

### 使用 Streamlit 網頁界面

本專案提供了一個基於 Streamlit 的網頁界面，讓您可以通過瀏覽器輕鬆使用轉錄和摘要功能：

1. 啟動 Streamlit 應用：

```bash
make streamlit
```

2. 在瀏覽器中打開顯示的 URL（通常是 http://localhost:8501）

3. 使用界面功能：
   - 在文本框中輸入 YouTube 影片網址
   - 點擊「Add to Queue」後即會透過 API 建立任務並自動排程背景處理
   - 若需要手動重新排程，可使用「Trigger Background Processing」按鈕
   - 查看處理進度和結果
   - 下載生成的摘要文件
   - 瀏覽本次會話的歷史記錄

Streamlit 界面特點：
- 直觀的用戶界面，無需命令行操作
- 新增任務後自動啟動背景處理，並提示鎖定狀態
- 實時顯示處理進度
- 直接在瀏覽器中查看摘要結果
- 列表可顯示並點擊每筆紀錄的 Notion URL；缺漏時會顯示提示，避免空白或死鏈接
- 一鍵下載摘要文件
- 保存會話歷史記錄，方便查看之前處理過的影片

與命令行版本的區別：
- Streamlit 版本不會自動刪除原始影片文件
- 提供了視覺化的處理進度
- 支持在瀏覽器中直接預覽摘要內容
### 啟動 FastAPI 任務 API

這個 API 提供 `POST /tasks` 與 `POST /processing-jobs` 端點，分別用於排程新任務與觸發背景處理。

1. 啟動開發伺服器：

```bash
make api
```

服務會在 `http://localhost:8080` 提供 API。

2. 送出新增任務請求：

```bash
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "db_type": "sqlite"}'
```

成功回應範例：

```json
{
  "task_id": "1",
  "status": "Pending",
  "db_type": "sqlite",
  "message": "Task queued successfully. Processing worker scheduled (worker: api-worker-123456).",
  "processing_started": true,
  "processing_worker_id": "api-worker-123456",
  "cached": false
}
```

#### 重複提交行為

API 會自動對同一 URL 進行去重：

- **已完成且在 TTL 內**（預設 1 小時）：回傳 `200 OK`，`cached: true`，直接返回先前的處理結果。
- **正在處理中或排隊中**（Pending / Processing）：回傳 `409 Conflict`。
- **無紀錄 / 已過期 / 曾失敗**：正常建立新 Task，回傳 `201 Created`。

TTL 可透過環境變數 `TASK_CACHE_TTL_SECONDS` 調整（預設 3600 秒）。

## 瀏覽器外掛（Chrome/Edge）

可使用瀏覽器外掛直接在 YouTube 影片頁或列表連結送出摘要任務，免手動複製網址。

### 安裝（開發模式）

1. 開啟 Chrome/Edge 擴充功能管理頁
   - Chrome: `chrome://extensions/`
   - Edge: `edge://extensions/`
2. 啟用「開發人員模式」
3. 點擊「載入未封裝項目」並選擇資料夾：`src/apps/extension/`

### 設定

1. 在擴充功能列表中點擊「詳細資料」→「擴充功能選項」
2. 設定 API Base URL（預設 `http://localhost:8080`）

### 使用方式

- 在 YouTube 影片頁點擊工具列的外掛按鈕，即可送出任務
- 在 YouTube 列表中的影片連結上按右鍵，選擇「Send YouTube link to Whisper Summary」
- 成功/失敗會顯示通知訊息

> 注意：若要寫入 Notion，必須在 `.env` 中設定 `NOTION_API_KEY` 與 `NOTION_DATABASE_ID`，缺漏時 API 會回傳 400 錯誤。若希望 Discord 通知附上 Notion 頁面連結，請額外設定 `NOTION_URL`（例如 `https://www.notion.so/your-workspace`）。

3. 觸發背景處理流程：

```bash
curl -X POST http://localhost:8080/processing-jobs \
  -H "Content-Type: application/json" \
  -d '{"db_type": "sqlite"}'
```

成功回應會立即回傳 202 Accepted，內容如下：

```json
{
  "worker_id": "api-worker-123456",
  "db_type": "sqlite",
  "accepted": true,
  "message": "Processing worker scheduled."
}
```

如果已經有 worker 正在處理，API 會回傳 409 Conflict 並附上 `Processing already running.` 提示。
新的 worker 會持續撈取佇列直到沒有可執行的任務，處理期間新增的任務也會在同一輪內完成。

### 4. 查詢與釋放 processing lock（維運專用）

當 `/processing-jobs` 回傳 `Processing already running.`，表示全域鎖仍由某個 worker 持有；此時可用下列維運端點查詢或強制釋放：

- `GET /processing-lock`
  - 回傳 lock 狀態（持有者、最後更新時間、是否超過 `PROCESSING_LOCK_TIMEOUT_SECONDS`）。
  - 需要附帶 `X-Maintainer-Token: ${PROCESSING_LOCK_ADMIN_TOKEN}` header。
  - 範例：

    ```bash
    curl http://localhost:8080/processing-lock \
      -H "X-Maintainer-Token: ${PROCESSING_LOCK_ADMIN_TOKEN}"
    ```

- `DELETE /processing-lock`
  - 詢問後釋放 lock；若 `expected_worker_id` 與目前持有者一致則直接釋放。
  - 可加入 `force=true`（需 `force_threshold_seconds`）來清除停滯的 lock，或 `dry_run=true` 先預檢。
  - 需要 `X-Maintainer-Token` header。
  - 範例：先查詢持有者，再確認一致後釋放：

    ```bash
    curl -X DELETE http://localhost:8080/processing-lock \
      -H "Content-Type: application/json" \
      -H "X-Maintainer-Token: ${PROCESSING_LOCK_ADMIN_TOKEN}" \
      -d '{"expected_worker_id": "api-worker-123", "reason": "recovery after crash"}'
    ```

  - 若要強制清除鎖，請另外提供 `force=true` 與 `force_threshold_seconds`（以秒為單位）：

    ```bash
    curl -X DELETE http://localhost:8080/processing-lock \
      -H "Content-Type: application/json" \
      -H "X-Maintainer-Token: ${PROCESSING_LOCK_ADMIN_TOKEN}" \
      -d '{"force": true, "force_threshold_seconds": 1200, "reason": "stale worker cleanup"}'
    ```

    這個流程會先確認鎖已經停滯超過設定秒數才會真正 clear，避免誤殺活著的 worker。

請將 `PROCESSING_LOCK_ADMIN_TOKEN` 設定在 `.env` 中，此值即為上述 `X-Maintainer-Token` 的內容，僅限內部維運人員使用；Streamlit 維運介面會自動套用該設定，不需額外輸入。

若想於 Docker 環境啟動 API，可直接執行 `docker compose up -d api`（或在 `api` 容器內跑 `make api`），API 會綁定宿主機的 8080 連接埠。

## 使用 Ollama (本地模型)

如果您想使用 Ollama 進行本地摘要處理，請先設置 Ollama：

1. 下載並安裝 Ollama：https://github.com/ollama/ollama

2. 啟動 Ollama 服務：

```bash
ollama serve
```

3. 拉取 Llama 3.2 模型：

```bash
ollama pull llama3.2
```

4. 在 `src/infrastructure/llm/summarizer_service.py` 中調整 `summarize` 方法即可強制改用 Ollama：

```python
def summarize(self, title, text):
    return self.summarize_with_ollama(title, text)
```

## 輸出結果

處理完成後，摘要文件將保存在 `data/summaries/` 目錄下，檔名格式為：
`_summarized_YYYYMMDDHHMMSS_<YouTubeID>_影片標題.md`。

說明：
- 每次處理都加入時間戳與 YouTube 影片 ID，避免同標題重複覆蓋。
- 範例：`_summarized_20250101T123000_dQw4w9WgXcQ_我的筆記.md`

摘要內容以 Markdown 格式呈現，包含：
- 完整資訊與重要細節
- 結構化的內容整理
- 關鍵洞察與見解

## 自定義設置

### 修改 Whisper 模型大小

在 `src/core/config.py` 中可調整 `Config.transcription_model_size`，例如：

```python
self.transcription_model_size = "base"  # 可選: tiny, base, small, medium, large
```

### 修改摘要提示詞

在 `src/core/prompt.py` 中自定義摘要提示詞模板（`PROMPT_3`）。

## 開發相關

### 開發指令

- **執行測試**: `make test`
- **Lint**: `uv run flake8 .`
- **格式化**: `ruff format .`（若需）
- **啟動 REST API**: `make api`（啟動 `src/apps/api/main.py` 內的 FastAPI）

```
CODEX_HOME="$PWD/.codex" codex
```

### 更新依賴

若新增或更新依賴項，請更新 `pyproject.toml` 後鎖定版本：

```bash
uv lock
```
