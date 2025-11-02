# YouTube 影片文字轉錄與摘要工具

此專案是一個專為內容創作者、研究人員和學習者設計的 YouTube 影片文字轉錄與摘要工具。它能自動下載 YouTube 影片、提取音訊、進行高精度語音轉文字，並利用先進的大型語言模型（LLM）生成結構化摘要，幫助用戶快速理解和提取影片中的關鍵信息。

## 專案架構與工作流程

本工具採用模組化設計，主要由以下核心組件構成：

- **`transcriber.py`**: 處理影片轉錄邏輯。
- **`summarizer.py`**: 處理文字摘要邏輯。
- **`api/server.py`**: 提供 FastAPI HTTP API，對外開放新增任務的端點。
- **`streamlit_app.py`**: 包含所有 UI 相關程式碼。
- **`youtube_downloader.py`**: 管理影片下載內容。
- **`processing.py`**: 處理單個文件的轉錄和摘要流程。
- **`file_manager.py`**: 處理文件操作，如保存和刪除。
- **`summary_storage.py`**: 將摘要保存到 Notion 等外部平台。

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
```

### 2. 啟動 Docker 服務

在專案根目錄執行：

```bash
docker compose up -d
```

此指令會啟動 Docker 容器，包括主要的應用服務 (app service)。
- 預設對外開放 8501（Streamlit）與 8080（FastAPI）。

### 3. 進入應用服務

```bash
docker compose exec app bash
```

### 4. 安裝依賴

進入 app 服務後，安裝所需的依賴項：

```bash
make install
```

此指令會：
- 下載並安裝最新版本的 yt-dlp 到 /usr/local/bin/
- 設置 yt-dlp 的執行權限
- 安裝 requirements.txt 中列出的 Python 依賴

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
或
```bash
python main.py
```

### 一鍵完成整個流程

下載影片並立即進行處理：

```bash
make auto url="YOUR_YOUTUBE_URL"
```

### 使用 Streamlit 網頁界面

本專案提供了一個基於 Streamlit 的網頁界面，讓您可以通過瀏覽器輕鬆使用轉錄和摘要功能：

1. 啟動 Streamlit 應用：

```bash
streamlit run streamlit_app.py
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
  "processing_worker_id": "api-worker-123456"
}
```

> 注意：若要寫入 Notion，必須在 `.env` 中設定 `NOTION_API_KEY` 與 `NOTION_DATABASE_ID`，缺漏時 API 會回傳 400 錯誤。

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

若想於 Docker 環境啟動，可先進入 `app` 服務：`docker compose exec app bash -lc "make api"`，API 會同樣綁定宿主機的 8080 連接埠。

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

4. 在 summarizer.py 中修改 summarize 方法以使用 Ollama：

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

在 main.py 中，可以修改 Transcriber 的模型大小：

```python
transcriber = Transcriber(model_size="base")  # 可選: tiny, base, small, medium, large
```

### 修改摘要提示詞

在 prompt.py 中，可以自定義摘要的提示詞模板。

## 開發相關

### 開發指令

- **執行測試**: `pytest`
- **檢查程式碼風格**: `ruff check .`
- **格式化程式碼**: `ruff format .`
- **啟動 REST API**: `make api`（啟動 FastAPI 伺服器於 http://localhost:8080）

### 更新依賴

若新增或更新依賴項，請執行以下指令來更新 `requirements.txt`：

```bash
pip freeze > requirements.txt
```
