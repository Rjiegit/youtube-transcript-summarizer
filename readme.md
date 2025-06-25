# YouTube 影片文字轉錄與摘要工具

此專案是一個專為內容創作者、研究人員和學習者設計的 YouTube 影片文字轉錄與摘要工具。它能自動下載 YouTube 影片、提取音訊、進行高精度語音轉文字，並利用先進的大型語言模型（LLM）生成結構化摘要，幫助用戶快速理解和提取影片中的關鍵信息。

## 專案架構與工作流程

本工具採用模組化設計，主要由以下核心組件構成：

- **主控制器 (Main)**: 負責協調整個應用程序的工作流程
- **處理器 (Processor)**: 處理單個文件的轉錄和摘要流程
- **轉錄器 (Transcriber)**: 使用 OpenAI 的 Whisper 模型將音訊轉換為文字
- **摘要生成器 (Summarizer)**: 使用 LLM (如 Google Gemini、OpenAI GPT 或本地 Ollama) 生成摘要
- **文件管理器 (FileManager)**: 處理文件操作，如保存和刪除
- **摘要存儲器 (SummaryStorage)**: 將摘要保存到 Notion 等外部平台

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
   - 點擊「開始分析」按鈕開始處理
   - 查看處理進度和結果
   - 下載生成的摘要文件
   - 瀏覽本次會話的歷史記錄

Streamlit 界面特點：
- 直觀的用戶界面，無需命令行操作
- 實時顯示處理進度
- 直接在瀏覽器中查看摘要結果
- 一鍵下載摘要文件
- 保存會話歷史記錄，方便查看之前處理過的影片

與命令行版本的區別：
- Streamlit 版本不會自動刪除原始影片文件
- 提供了視覺化的處理進度
- 支持在瀏覽器中直接預覽摘要內容

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

處理完成後，摘要文件將保存在 `data/` 目錄下，檔名格式為：`_summarized_YYYYMMDDHHMMSS_影片標題.md`。

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

### 更新依賴

若新增或更新依賴項，請執行以下指令來更新 `requirements.txt`：

```bash
pip freeze > requirements.txt
```
