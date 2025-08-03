# Project Brief

## YouTube 影片文字轉錄與摘要工具

**目標**: 自動化 YouTube 影片處理流程，從下載到生成結構化摘要的完整解決方案

**核心功能**:
- YouTube 影片自動下載與音訊提取
- 使用 OpenAI Whisper 進行高精度語音轉文字
- 利用多種 LLM (OpenAI GPT, Google Gemini, Ollama) 生成智能摘要
- 支援中文內容優化，輸出 Markdown 格式摘要
- 可選擇將摘要存儲到 Notion 等外部平台

**目標用戶**: 內容創作者、研究人員、學習者

**專案範圍**:
- 模組化架構設計，便於維護和擴展
- Docker 容器化部署，確保環境一致性
- 完整的測試覆蓋率，包括單元測試和集成測試
- 支援多種音訊/影片格式 (mp3, mp4, m4a, webm)
- 靈活的 LLM 配置選項