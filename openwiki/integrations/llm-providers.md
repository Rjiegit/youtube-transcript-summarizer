---
type: integration
title: LLM Providers、選擇與 Failover
description: 說明 Gemini、OpenAI、Ollama 的候選資格、加權選擇、provider 呼叫與一次性 transient failover。
tags: [llm, gemini, openai, ollama, failover]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-31T13:51:03.458Z
sources:
  - id: openwiki-source-36d48d46c256392dc902bc2d
    resource: repo://src/infrastructure/llm/model_options.py
  - id: openwiki-source-a1071f6de2071698b70c8d14
    resource: repo://src/infrastructure/llm/summarizer_service.py
  - id: openwiki-source-791a1bcc2cae6ed2d067dedb
    resource: repo://src/infrastructure/llm/weighted_selection.py
  - id: openwiki-source-df04114da62d5e054970a89f
    resource: repo://src/services/pipeline/processing_runner.py
  - id: openwiki-source-7def47d9e5d7b25e40812c7c
    resource: repo://tests/test_summarizer_service.py
  - id: openwiki-source-e2ee026fbcf730652e2c0e63
    resource: repo://tests/test_weighted_selection.py
generated: { by: "codex", at: "2026-08-31T13:51:03.458Z" }
---

# LLM Providers、選擇與 Failover

`Summarizer` 對 processing pipeline 提供單一 `summarize(title, text, metadata=None)` 能力，內部再選擇 Gemini、OpenAI 或 Ollama。Provider selection、prompt construction 與 transient failover 都由 LLM infrastructure 層擁有，worker 只讀取最後成功的 provider/model label 用於輸出紀錄。

## 候選池與資格

每個 `ModelCandidate` 包含 backend、model 與正權重。候選池建構時拒絕空池、未知 backend、空 model、bool/非數字或非正 weight，以及重複的 `provider:model`。實際選擇會先排除本次已失敗的 candidate，再移除沒有 credential 的 backend，最後只對剩餘權重重新計算隨機分布。

Provider 的可用條件是：

- OpenAI：存在 `OPENAI_API_KEY`；
- Gemini：存在 `GOOGLE_GEMINI_API_KEY`；
- Ollama：存在 `OLLAMA_API_KEY`，client 另讀取 `OLLAMA_HOST`，預設為 `https://ollama.com`。

沒有 eligible candidate 時，selector 會以明確錯誤列出 configured candidates 與 unavailable backends。Credential 只讓 backend 具備入選資格，不會自動把 manifest 已安裝 provider 或任意模型加入候選池。

## 預設 weighted selection

預設自動池目前只有六個 Gemini models，權重是相對機率：

| Model | Weight | 理論比例 |
| --- | ---: | ---: |
| `gemini-3.7-flash` | 1 | 9.09% |
| `gemini-2.5-flash-lite` | 2 | 18.18% |
| `gemini-2.5-flash` | 1 | 9.09% |
| `gemini-3-flash-preview` | 1 | 9.09% |
| `gemini-3.1-flash-lite` | 3 | 27.27% |
| `gemini-3.5-flash-lite` | 3 | 27.27% |

Selector 每次 request 做一次 weighted random draw；它沒有紀錄已用 RPM、沒有跨 request quota state，也不保證短期分布。因此 model 註解中的 Max RPM 只是設定權重的依據，這個機制不是 rate limiter 或 quota scheduler。

## Provider 呼叫

共用 prompt 將 title、transcript 與受限的 creator metadata context 組成學習筆記指令。OpenAI 使用 `OpenAI(...).chat.completions.create`；Gemini 先 configure API key，再建立 `GenerativeModel`；Ollama 使用指定 host、Authorization header 與 client chat。成功後 `last_backend` 與 `last_model_label` 設為實際 provider 及 `provider:model`，worker 再組成 `faster-whisper-<size>+<provider:model>`。

Ollama import 是 optional guard：套件不可用時會保留明確 runtime error，而不是在 module import 階段讓所有其他 provider 無法使用。

## 一次性 failover

第一次 candidate 失敗時，只有被分類為 transient 的錯誤才會重選一次，且第二次排除原 candidate：

- OpenAI：rate limit、timeout、connection error 或 HTTP 5xx；
- Gemini：quota/resource exhausted、timeout、temporary unavailable/server 類錯誤；
- Ollama：timeout、connection、HTTP 429 或 5xx。

認證錯誤與一般 4xx 不切換 candidate，直接向上拋出。若沒有另一個 eligible candidate，重拋第一次的原始 exception；若 fallback candidate 也失敗，第二個 error 直接結束，不嘗試第三次。metadata context 在第一與第二個 candidate 間保持一致。

## 測試與擴充

Weighted selection tests 注入 deterministic RNG，分別驗證 validation、credential filtering、exclusion 與相對權重。Summarizer tests 對 fallback scenario 注入最小候選池，避免測試依賴預設池剛好只有 Gemini。新增 provider 時需要同步新增 backend enum、credential eligibility、provider call、transient classification、候選設定與 focused tests；只安裝 SDK 不會讓 provider 自動進入流量。

## 延伸閱讀

- [媒體轉錄與摘要流程](../workflows/media-processing.md)
- [模組邊界與外部依賴](../architecture/module-boundaries-and-dependencies.md)
- [設定、執行與部署](../operations/configuration-and-deployment.md)
- [測試策略與擴充指南](../testing/test-strategy.md)
