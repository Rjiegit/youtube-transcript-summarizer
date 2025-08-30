# Project Brief

## 專案概述

**YouTube Transcript Summarizer** 是一個自動化的影片內容處理系統，專門用於：

- 從 YouTube 影片提取高品質音訊轉錄
- 使用 AI 模型生成結構化中文摘要
- 提供多種使用介面（命令列、Streamlit Web 應用）
- 支援多種 LLM 供應商（OpenAI、Google Gemini、Ollama）

## 核心目標

1. **自動化工作流程**：從影片下載到摘要生成的端到端自動化
2. **高精度轉錄**：使用 OpenAI Whisper 模型確保轉錄品質
3. **智能摘要**：生成結構化、有洞察力的中文摘要
4. **靈活部署**：Docker 容器化，支援本地和雲端部署
5. **多元選擇**：支援多種 AI 模型和介面選項

## 專案範圍

- **輸入**：YouTube 影片 URL
- **處理**：音訊下載 → 語音轉錄 → AI 摘要
- **輸出**：Markdown 格式摘要檔案
- **存儲**：本地檔案系統 + 可選 Notion 整合