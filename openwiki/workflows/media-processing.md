---
type: workflow
title: 媒體轉錄與摘要流程
description: 追蹤單筆任務的下載、YouTube metadata 擷取、Whisper 轉錄、LLM 選擇、輸出儲存、通知與失敗處理。
tags: [pipeline, whisper, llm, metadata, storage]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-30T14:54:17.621Z
sources:
  - id: openwiki-source-0fdf5745e1f00e18dd400997
    resource: repo://src/core/prompt.py
  - id: openwiki-source-0a31e24491d869302652bc69
    resource: repo://src/domain/media/models.py
  - id: openwiki-source-36d48d46c256392dc902bc2d
    resource: repo://src/infrastructure/llm/model_options.py
  - id: openwiki-source-a1071f6de2071698b70c8d14
    resource: repo://src/infrastructure/llm/summarizer_service.py
  - id: openwiki-source-791a1bcc2cae6ed2d067dedb
    resource: repo://src/infrastructure/llm/weighted_selection.py
  - id: openwiki-source-bd11e0e09048def2f9ec2ff6
    resource: repo://src/infrastructure/media/downloader.py
  - id: openwiki-source-c58845fdbb50864c91205283
    resource: repo://src/infrastructure/storage/file_storage.py
  - id: openwiki-source-df04114da62d5e054970a89f
    resource: repo://src/services/pipeline/processing_runner.py
  - id: openwiki-source-839ded7442c98545a6825769
    resource: repo://tests/test_processing_worker.py
generated: { by: "codex", at: "2026-08-30T14:54:17.621Z" }
---

# 媒體轉錄與摘要流程

## 單筆處理順序

`ProcessingWorker._process_task` 是 pipeline owner，順序固定：

1. `YouTubeDownloader` 執行 yt-dlp，將媒體放在 `data/videos`，並回傳 path、title 與已整理的 `VideoMetadata`。
2. worker 以下載 title（fallback 到既有 title 或 URL）更新仍為 `Processing` 的 task。
3. `Transcriber` 以設定的 faster-whisper model 轉錄媒體。
4. `Summarizer` 將 title、逐字稿與可選的 metadata 套入學習筆記 prompt，再呼叫選定的 LLM。
5. worker 組合 `faster-whisper-<size>+<provider:model>` 模型標籤，以穩定 output path 保存 Markdown；有 metadata 時，另在實際 Markdown 路徑旁保存同 stem 的 `.metadata.json`。
6. `SummaryStorage` 建立 Notion page；若回傳 page id，寫回 task。
7. task 更新為 `Completed`，包含摘要、duration 與 Notion page id，最後送 Discord completion notification。

舊的 downloader adapter 或 test double 若未回傳 `VideoMetadata`，worker 仍以原本的兩參數介面呼叫 summarizer，且不寫 sidecar，保留向後相容行為。

一般步驟丟出 exception 時，task 會轉為 `Failed` 並保存 error message 與 elapsed duration，而 worker loop 仍可繼續下一筆。metadata sidecar 是特例：Markdown 成功後若 JSON 寫入失敗，只記錄 warning，仍繼續 Notion 保存與完成 task。通知在 task 已標為 Completed 後執行；通知本身若拋例外，現行外層 catch 仍會再把 task 改為 Failed，因此 notifier 實作應自行吸收可恢復的 delivery failure。

## 下載與 metadata 邊界

Downloader 一律使用 yt-dlp，輸出模板以 YouTube video id 命名，降低 title 字元造成的 path 不穩定。它透過帶 prefix 的 `--print` 行取得搬移後 path、title 與 JSON metadata，限制記錄的 subprocess output 長度，並在結果 path 不明時依 video id glob 尋找產物。metadata JSON 無法解析不會使有效下載失敗；系統仍用 URL、video id 與已解析 title 建立可用但欄位可能為空的 `VideoMetadata`。

傳入 domain 的資料不是完整 yt-dlp info dict，而是白名單 schema：source URL、video id、title、description、channel/channel id、upload date、duration、chapters、UTC extraction timestamp 與 schema version。`VideoMetadata.from_info_dict` 會去除空白字串、將 `YYYYMMDD` 日期正規化成 `YYYY-MM-DD`、拒絕 bool 或非數字 duration，並忽略缺 title 或 start time 的 chapter。這可避免 cookies、下載格式及其他未審查的 extractor 欄位進入 prompt 或 sidecar。

Transcriber 使用 faster-whisper，逐 segment 累積文字並可透過 Streamlit progress callback 呈現進度。這是重型本機 dependency；測試通常注入 fake factory，而不載入模型。

## Prompt 的 metadata trust boundary

逐字稿仍是摘要的主要事實來源。若有 metadata，`Summarizer` 只把頻道、上架日期、格式化時長、章節與 description 放入獨立的「創作者提供，僅供背景」區塊，並明示這些是不可信參考資料、不可視為逐字稿已證實的事實，也不得用其中指示改變任務、規則或輸出格式。

送入模型的 description 最多 6,000 個字元，超出時加上截斷標記；此限制只影響 prompt context，sidecar 仍由 `VideoMetadata.to_dict()` 保存完整的 curated description。相同 metadata 會隨第一次 candidate 與 transient failure 後的 fallback candidate 傳遞給 OpenAI、Gemini 或 Ollama provider。

## LLM weighted selection 與 failover

候選池在建構時驗證：不可為空、backend/model 必須有效、weight 必須為正數且 provider:model 不可重複。實際選擇先排除沒有 API key 的 backend 與已 excluded candidate，再對剩餘 weight 重新計算比例。

目前預設自動池只包含 Gemini，依模型 Max RPM 的相對比例設定六個候選：

| 模型 | 權重 | 理論選取占比 |
| --- | ---: | ---: |
| `gemini-3.7-flash` | 1 | 9.09% |
| `gemini-2.5-flash-lite` | 2 | 18.18% |
| `gemini-2.5-flash` | 1 | 9.09% |
| `gemini-3-flash-preview` | 1 | 9.09% |
| `gemini-3.1-flash-lite` | 3 | 27.27% |
| `gemini-3.5-flash-lite` | 3 | 27.27% |

這是每次摘要請求的加權隨機選擇：短期樣本可能偏離理論占比，也不會追蹤或強制各模型的 RPM。Provider credential 只讓該 backend 具備被選資格，不會把未列在 `AUTO_MODEL_CANDIDATES` 的 OpenAI、Ollama 或其他模型自動加入流量池。

成功選定後記錄 `last_backend` 與 `last_model_label`。只有 transient provider error 才做一次 fallback，且排除第一次失敗的 candidate：OpenAI rate limit/timeout/connection/5xx、Gemini quota/timeout/server errors、Ollama timeout/connection/429/5xx。認證與一般 4xx 直接向上拋出；沒有替代 candidate 時重拋原始 error；fallback 再失敗時也不嘗試第三次。

## 輸出、失敗語意與 extension seams

Markdown filename 由 title 與 URL 建立，`FileManager.save_text` 只清理 basename、保留 directory，建立缺少的目錄並以 UTF-8 寫入。`save_json` 也保留 directory，以 UTF-8、未 ASCII escape 且具縮排的 JSON 寫入；sidecar 名稱以 `save_text` 回傳的實際路徑為準，因此 Markdown filename 因長度被截斷時，兩者仍共享相同 stem。Notion summary 另以 1,800-character rich-text chunks 保存。

Worker constructor 可注入 downloader、transcriber、summarizer、summary storage、file manager、notifier 與 config factory。新增 media/LLM/storage implementation 時應遵守既有小介面並用 factory 注入，不必在 orchestration 中加入 test-specific branch。focused tests 分別驗證 yt-dlp metadata 白名單與解析降級、prompt 的 trust boundary 與 6,000 字元限制、Unicode JSON 與長檔名配對，以及 sidecar 寫入失敗仍完成 task。

## 延伸閱讀

- [任務生命週期與併發控制](task-lifecycle.md)
- [Notion 資料整合](../integrations/notion-and-showcase.md)
- [設定、執行與部署](../operations/configuration-and-deployment.md)
- [測試策略與擴充指南](../testing/test-strategy.md)
