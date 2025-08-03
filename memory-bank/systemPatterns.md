# System Patterns

## 架構設計模式

### 依賴注入模式 (Dependency Injection)
- **Main** 類別使用依賴注入接收所有組件
- 支援測試時注入 mock 對象
- 提高組件間的解耦性

### 介面分離模式 (Interface Segregation)
- `TranscriberInterface`: 定義轉錄行為
- `SummarizerInterface`: 定義摘要生成行為
- `FileManagerInterface`: 定義文件操作行為
- `SummaryStorageInterface`: 定義存儲行為

### 單一職責模式 (Single Responsibility)
- **Processor**: 負責單一文件的處理流程
- **Transcriber**: 專注於語音轉文字
- **Summarizer**: 專注於摘要生成
- **FileManager**: 專注於文件操作
- **SummaryStorage**: 專注於摘要存儲
- **Config**: 集中化配置管理

### 工廠模式變體
- **Summarizer** 根據可用 API 金鑰選擇 LLM 供應商
- **Transcriber** 支援多種 Whisper 實現 (faster-whisper, original whisper)

### 錯誤處理模式
- 漸進式降級: OpenAI → Gemini → Ollama
- 詳細的錯誤記錄和用戶反饋
- 優雅的錯誤恢復機制

### 配置模式
- 環境變數優先，後備預設值
- 中央化配置類別
- 自動目錄創建和驗證

### 容器化模式
- Docker Compose 編排
- 環境隔離和一致性
- 簡化部署和依賴管理