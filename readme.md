# YouTube Transcript Summarizer

此專案是一個簡單的 YouTube 文字轉錄摘要工具。
利用 Docker 容器與 Ollama 的 Llama 模型進行影片文字生成與摘要。請遵循以下步驟來設定開發環境並運行應用程式。

## 專案需求
- Docker Compose
- Ollama 服務 (https://github.com/ollama/ollama)

## 環境設置

1. 確保系統已安裝 Docker 和 Docker Compose。這將用於啟動應用程式的 Docker 容器化環境。
2. 安裝並啟動 Ollama，用於下載和使用 Llama 模型來進行文字摘要處理。

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

### 執行 YouTube 文字轉錄摘要

待環境設置完成後，可以在容器中執行 Python 腳本來處理 YouTube 影片文字轉錄並生成摘要。

1. 進入 Docker 容器中的 app 服務。
2. 執行轉錄與摘要腳本，具體指令會根據腳本設計有所不同，例如：
```bash
python main.py "youtube_video_url"
```

此指令會自動下載指定 YouTube 影片的文字內容，並利用 Ollama 的 Llama 模型進行摘要處理。