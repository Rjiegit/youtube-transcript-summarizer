---
type: workflow
title: 媒體轉錄與摘要流程
description: 追蹤單筆任務的下載、Whisper 轉錄、LLM 選擇、輸出儲存、通知與失敗處理。
tags: [pipeline, whisper, llm, storage]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-29T14:03:31.952Z
sources:
  - id: openwiki-source-a1071f6de2071698b70c8d14
    resource: repo://src/infrastructure/llm/summarizer_service.py
  - id: openwiki-source-791a1bcc2cae6ed2d067dedb
    resource: repo://src/infrastructure/llm/weighted_selection.py
  - id: openwiki-source-df04114da62d5e054970a89f
    resource: repo://src/services/pipeline/processing_runner.py
generated: { by: "codex", at: "2026-08-29T14:03:31.952Z" }
---

# 媒體轉錄與摘要流程

## 單筆處理順序

`ProcessingWorker._process_task` 是 pipeline owner，順序固定：

1. `YouTubeDownloader` 執行 yt-dlp，將媒體放在 `data/videos` 並回傳 path/title。
2. worker 以下載 title（fallback 到既有 title 或 URL）更新仍為 `Processing` 的 task。
3. `Transcriber` 以設定的 faster-whisper model 轉錄媒體。
4. `Summarizer` 將 title 與逐字稿套入學習筆記 prompt，呼叫選定 LLM。
5. worker 組合 `faster-whisper-<size>+<provider:model>` 模型標籤，以穩定 output path 保存 Markdown。
6. `SummaryStorage` 建立 Notion page；若回傳 page id，寫回 task。
7. task 更新為 `Completed`，包含摘要、duration 與 Notion page id，最後送 Discord completion notification。

任何步驟丟出 exception 都會跳過後續步驟，task 轉為 `Failed` 並保存 error message 與 elapsed duration。通知在 task 已標為 Completed 後執行；通知本身若拋例外，現行 catch 仍會再把 task 改為 Failed，因此 notifier 實作應自行吸收可恢復的 delivery failure。

## 下載與轉錄

Downloader 一律使用 yt-dlp，輸出模板以 YouTube video id 命名，降低 title 字元造成的 path 不穩定。它限制記錄的 subprocess output 長度，並在結果 path 不明時依 video id glob 尋找產物。

Transcriber 使用 faster-whisper，逐 segment 累積文字並可透過 Streamlit progress callback 呈現進度。這是重型本機 dependency；測試通常注入 fake factory，而不載入模型。

## LLM weighted selection 與 failover

候選池在建構時驗證：不可為空、backend/model 必須有效、weight 必須為正數且 provider:model 不可重複。實際選擇先排除沒有 API key 的 backend 與已 excluded candidate，再對剩餘 weight 重新計算比例。

成功選定後記錄 `last_backend` 與 `last_model_label`。只有 transient provider error 才做一次 fallback，且排除第一次失敗的 candidate：OpenAI rate limit/timeout/connection/5xx、Gemini quota/timeout/server errors、Ollama timeout/connection/429/5xx。認證與一般 4xx 直接向上拋出；沒有替代 candidate 時重拋原始 error；fallback 再失敗時也不嘗試第三次。

## 輸出與 extension seams

Markdown filename 由 title 與 URL 建立，`FileManager` 只清理 basename、保留 directory，建立缺少的目錄並以 UTF-8 寫入。Notion summary 另以 1,800-character rich-text chunks 保存。

Worker constructor 可注入 downloader、transcriber、summarizer、summary storage、file manager、notifier 與 config factory。新增 media/LLM/storage implementation 時應遵守既有小介面並用 factory 注入，不必在 orchestration 中加入 test-specific branch。

## 延伸閱讀

- [任務生命週期與併發控制](task-lifecycle.md)
- [Notion 資料整合](../integrations/notion-and-showcase.md)
- [設定、執行與部署](../operations/configuration-and-deployment.md)
