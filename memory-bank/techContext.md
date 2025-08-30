# Tech Context

## 技術棧

### 核心語言與框架
- **Python 3.11**: 主要開發語言
- **Streamlit**: Web 應用框架
- **Docker**: 容器化部署
- **Docker Compose**: 多服務編排

### AI/ML 技術棧
- **OpenAI Whisper**: 語音轉文字模型
  - 標準版: `openai-whisper`
  - 高效版: `faster-whisper`
  - 模型大小: tiny, base, small, medium, large
- **LLM 供應商**:
  - **Google Gemini**: 主要摘要模型 (gemini-2.0-flash)
  - **OpenAI GPT**: 備選摘要模型 (gpt-4o-mini)
  - **Ollama**: 本地模型支援 (llama3.2)

### 媒體處理
- **yt-dlp**: YouTube 影片下載
- **FFmpeg**: 音訊/影片處理
- **PyTube/PyTubeFix**: Python YouTube API

### 資料存儲
- **本地檔案系統**: Markdown 格式摘要
- **Notion API**: 雲端知識庫整合

## 開發工具

### 建構與部署
- **Makefile**: 自動化建構腳本
- **pip**: Python 套件管理
- **requirements.txt**: 依賴管理

### 測試框架
- **unittest**: Python 標準測試框架
- **GitHub Actions**: CI/CD 自動化
- **flake8**: 程式碼品質檢查

### 開發環境
- **VS Code**: 主要 IDE
- **Docker Dev Container**: 一致的開發環境
- **Debian 12 (Bookworm)**: 容器基礎系統

## 環境配置

### 必要依賴
```bash
# 系統級依賴
apt install ffmpeg git make curl pkg-config build-essential

# Python 依賴
pip install -r requirements.txt

# yt-dlp 安裝
curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
```

### API 金鑰配置
```env
# .env 檔案
OPENAI_API_KEY=your_openai_api_key
GOOGLE_GEMINI_API_KEY=your_gemini_api_key
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_notion_database_id
```

## 技術限制與約束

### 效能限制
- **Whisper 模型**: CPU/GPU 資源需求高
- **檔案大小**: 建議單檔不超過 2GB
- **處理時間**: 約為原影片時長的 10-20%

### API 限制
- **Google Gemini**: 有 API 調用頻率限制
- **OpenAI**: 有 token 數量和費用限制
- **YouTube**: yt-dlp 可能因網站更新而失效

### 系統限制
- **檔名長度**: Linux 系統 255 bytes 限制
- **Unicode 支援**: 中文檔名需特殊處理
- **磁碟空間**: 影片檔案佔用空間大

## 安全考量

### 金鑰管理
- API 金鑰存儲在 `.env` 檔案中
- 絕不將金鑰提交到版本控制
- 使用 `.env.example` 提供範本

### 檔案安全
- 自動刪除處理完的影片檔案
- 檔名清理防止路徑注入
- 權限控制確保檔案安全

## 部署架構

### Docker 部署
```yaml
services:
  app:
    build: ./.docker
    volumes:
      - ./:/usr/src/app
    ports:
      - "8501:8501"  # Streamlit
```

### 本地開發
- 直接運行 Python 腳本
- 使用 Makefile 簡化操作
- VS Code Dev Container 支援

## 監控與日誌

- **Logger 類**: 統一日誌格式
- **錯誤追蹤**: 詳細的錯誤資訊記錄
- **效能監控**: 處理時間統計
- **檔案追蹤**: 處理檔案的完整生命週期記錄