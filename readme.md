# YouTube Transcript Summarizer

此專案是一個 YouTube 影片文字轉錄與摘要工具，利用 Whisper 模型進行語音轉文字，並透過 LLM (大型語言模型) 生成結構化摘要。整個流程在 Docker 容器中運行，確保環境一致性與易於部署。

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