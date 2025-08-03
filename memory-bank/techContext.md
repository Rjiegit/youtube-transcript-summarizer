# Tech Context

## 技術堆疊

### 核心技術
- **Python 3.x**: 主要開發語言
- **OpenAI Whisper**: 語音轉文字引擎
  - `faster-whisper`: 優化版本，更快的推理速度
  - `openai-whisper`: 原版實現
- **LLM 整合**: 
  - OpenAI GPT API
  - Google Gemini API
  - Ollama (本地模型)

### 音訊/影片處理
- **yt-dlp**: YouTube 影片下載
- **pytube**: 備用下載器
- **支援格式**: mp3, mp4, m4a, webm

### 資料儲存與管理
- **檔案系統**: 本地 Markdown 檔案儲存
- **Notion API**: 可選的雲端知識庫整合
- **目錄結構**:
  - `data/videos/`: 原始影片檔案
  - `data/_summarized/`: 處理後的摘要檔案

### 開發與部署
- **Docker & Docker Compose**: 容器化部署
- **pytest**: 測試框架
- **unittest.mock**: 模擬測試
- **python-dotenv**: 環境變數管理

### 依賴套件 (主要)
```
openai-whisper==20240930
faster-whisper==1.0.3
openai==1.52.2
google-generativeai==0.8.3
notion-client==2.2.1
yt-dlp (最新版本)
pytube==15.0.0
```

### 系統約束
- **記憶體**: Whisper 模型需要足夠 RAM
- **儲存空間**: 影片和模型檔案
- **網路**: API 呼叫和影片下載
- **API 限制**: 各 LLM 供應商的速率限制

### 安全考量
- API 金鑰透過環境變數管理
- 不在程式碼庫中儲存機密資訊
- `.env.example` 提供範本

### 測試策略
- 單元測試覆蓋所有核心組件
- Mock 外部服務 (OpenAI, Gemini, Notion)
- 集成測試驗證組件互動
- 錯誤場景測試