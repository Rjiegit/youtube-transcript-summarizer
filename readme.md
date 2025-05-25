# YouTube Transcript Summarizer

此專案是一個簡單的 YouTube 文字轉錄摘要工具。
利用 Docker 容器與 LLM 進行影片文字生成與摘要。請遵循以下步驟來設定開發環境並運行應用程式。

## 專案需求
- Docker Compose
- OpenAI API Key(optional)
- Google Gemini API Key(optional)
- Ollama(optional) (https://github.com/ollama/ollama)

## 快速開始

### 啟動服務

在專案根目錄中執行以下指令，以後台模式啟動 Docker Compose 服務：

```bash
docker compose up -d
```

此指令會啟動 Docker 容器，包括主要的應用服務 (app service)，用於執行 Python 腳本來進行文字轉錄與摘要。

### 進入應用服務

進入 Docker 容器內部的 app 服務，進行進一步設置或執行操作：

```bash
docker compose exec app bash
```

### 安裝 Python 依賴

進入 app 服務後，安裝 Python 所需的依賴項。所有依賴項已列在 `requirements.txt` 中，請使用以下指令進行安裝：

```bash
pip install -r requirements.txt
```

若新增或更新依賴項，請執行以下指令來更新 `requirements.txt`：

```bash
pip freeze > requirements.txt
```


### OpenAI API

設定 OpenAI API Key

```
// .env
OPENAI_API_KEY=YOUR_KEY
```

### Google Gemini API

設定 Google Gemini API Key

```
// .env
GOOGLE_GEMINI_API_KEY=YOUR_KEY
```

### Ollama 設置

請先下載並啟動 Ollama 服務，然後下載所需的模型。

1. 啟動 Ollama 服務：

```bash
ollama serve
```

2. 拉取 Llama 3.2 模型，供文字轉錄摘要使用：

```bash
ollama pull llama3.2
```

## 使用方法

### 1. 下載 YouTube 影片音訊

請先將欲處理的 YouTube 影片音訊下載至 `data/videos/` 目錄。你可以使用 `yt-dlp` 工具，或直接使用 Makefile 指令：

```bash
make yt-dlp url="YOUR_URL"
```

此指令會自動將指定 YouTube 影片的音訊下載到 `data/videos/` 目錄下。

---

### 2. 執行文字轉錄與摘要

在 app 服務容器內，執行主程式：

```bash
make run
```
或
```bash
python main.py
```

此指令會自動處理 `data/videos/` 目錄下的音訊檔案，進行文字轉錄並利用 LLM 進行摘要處理。

---
