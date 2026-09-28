---
type: integration
title: LLM Providers、選擇與 Failover
description: 說明 Gemini、OpenAI、Ollama、Codex CLI 的候選資格、加權選擇、provider 呼叫與一次性 transient failover。
tags: [llm, gemini, openai, ollama, codex, failover]
verified:
  - by: openwiki/0.4.3
    at: 2026-09-28T16:59:07.681Z
sources:
  - id: openwiki-source-cd3c19edb3412c855091bcd0
    resource: repo://apps/whisper_summary/infrastructure/llm/model_options.py
  - id: openwiki-source-ef820dbbe7cff90830a1c016
    resource: repo://apps/whisper_summary/infrastructure/llm/prompt_context.py
  - id: openwiki-source-e207b6167639ff1973fe1237
    resource: repo://apps/whisper_summary/infrastructure/llm/summarizer_service.py
  - id: openwiki-source-25d6d487d3ae6567d7b0397b
    resource: repo://apps/whisper_summary/infrastructure/llm/weighted_selection.py
  - id: openwiki-source-5d30f93453a5fc9227aa0b47
    resource: repo://apps/whisper_summary/services/pipeline/processing_runner.py
  - id: openwiki-source-5882e8a0d3ce6c6d6fd7381f
    resource: repo://apps/whisper_summary/tests/unit/test_summarizer_service.py
  - id: openwiki-source-e17149958db116451aa12495
    resource: repo://apps/whisper_summary/tests/unit/test_weighted_selection.py
generated: { by: "codex", at: "2026-09-27T11:42:53.431Z" }
---

# LLM Providers、選擇與 Failover

`Summarizer` 對 processing pipeline 提供單一 `summarize(title, text, metadata=None)` 能力，內部再選擇 Gemini、OpenAI、Ollama 或 Codex CLI。Provider selection、prompt construction 與 transient failover 都由 LLM infrastructure 層擁有，worker 只讀取最後成功的 provider/model label 用於輸出紀錄。

## 候選池與資格

每個 `ModelCandidate` 包含 backend、model 與正權重。候選池建構時拒絕空池、未知 backend、空 model、bool/非數字或非正 weight，以及重複的 `provider:model`。實際選擇會先排除本次已失敗的 candidate，再移除不可用的 backend，最後只對剩餘權重重新計算隨機分布。

Provider 的可用條件是：

- OpenAI：存在 `OPENAI_API_KEY`；
- Gemini：存在 `GOOGLE_GEMINI_API_KEY`；
- Ollama：存在 `OLLAMA_API_KEY`，client 另讀取 `OLLAMA_HOST`，預設為 `https://ollama.com`。
- Codex CLI：`CODEX_BIN` 指向的執行檔可在 PATH 找到；不依賴上述 API keys。

沒有 eligible candidate 時，selector 會以明確錯誤列出 configured candidates 與 unavailable backends。Credential 只讓 backend 具備入選資格，不會自動把 manifest 已安裝 provider 或任意模型加入候選池。

## 預設 weighted selection

預設自動池包含六個 Gemini models 及一個 `codex_cli:gpt-6-luna`，權重合計 100。兩種 backend 都可用時，權重數值可直接讀為初次抽選百分比：Luna 90%，Gemini 合計 10%。只有 Gemini 可用時，六個 Gemini 模型會按其 10 點權重重新正規化。

| Model | Weight | 兩種 backend 都可用 | 僅 Gemini 可用 |
| --- | ---: | ---: | ---: |
| `gemini-3.7-flash` | 0.91 | 0.91% | 9.1% |
| `gemini-2.5-flash-lite` | 1.82 | 1.82% | 18.2% |
| `gemini-2.5-flash` | 0.91 | 0.91% | 9.1% |
| `gemini-3-flash-preview` | 0.91 | 0.91% | 9.1% |
| `gemini-3.1-flash-lite` | 2.73 | 2.73% | 27.3% |
| `gemini-3.5-flash-lite` | 2.72 | 2.72% | 27.2% |
| `codex_cli:gpt-6-luna` | 90 | 90% | 不可用 |

Selector 每次 request 做一次 weighted random draw；它沒有紀錄已用 RPM、沒有跨 request quota state，也不保證短期分布。因此 model 註解中的 Max RPM 只是設定權重的依據，這個機制不是 rate limiter 或 quota scheduler。

## Provider 呼叫

共用 prompt 將 title、transcript 與受限的 creator metadata context 組成學習筆記指令。OpenAI 使用 `OpenAI(...).chat.completions.create`；Gemini 先 configure API key，再建立 `GenerativeModel`；Ollama 使用指定 host、Authorization header 與 client chat。成功後 `last_backend` 與 `last_model_label` 設為實際 provider 及 `provider:model`，worker 再組成 `faster-whisper-<size>+<provider:model>`。

Ollama import 是 optional guard：套件不可用時會保留明確 runtime error，而不是在 module import 階段讓所有其他 provider 無法使用。

Codex CLI 以 `codex exec --ephemeral --ignore-user-config --sandbox read-only --model ... -` 接收 prompt，並讀取 stdout 作為摘要；執行時移除子程序環境中的敏感 credential 變數。`CODEX_TIMEOUT_SECONDS` 預設 900 秒且必須為正整數。非零結束碼或空輸出會使 task 失敗。

## 一次性 failover

第一次 candidate 失敗時，只有被分類為 transient 的錯誤才會重選一次，且第二次排除原 candidate：

- OpenAI：rate limit、timeout、connection error 或 HTTP 5xx；
- Gemini：quota/resource exhausted、timeout、temporary unavailable/server 類錯誤；
- Ollama：timeout、connection、HTTP 429 或 5xx。
- Codex CLI：timeout；一般非零結束碼不視為 transient。

認證錯誤與一般 4xx 不切換 candidate，直接向上拋出。若沒有另一個 eligible candidate，重拋第一次的原始 exception；若 fallback candidate 也失敗，第二個 error 直接結束，不嘗試第三次。metadata context 在第一與第二個 candidate 間保持一致。

## 測試與擴充

Weighted selection tests 注入 deterministic RNG，分別驗證 validation、credential filtering、exclusion 與相對權重。Summarizer tests 對 fallback scenario 注入最小候選池，避免測試依賴預設池剛好只有 Gemini。新增 provider 時需要同步新增 backend enum、credential eligibility、provider call、transient classification、候選設定與 focused tests；只安裝 SDK 不會讓 provider 自動進入流量。

## 延伸閱讀

- [媒體轉錄與摘要流程](../workflows/media-processing.md)
- [模組邊界與外部依賴](../architecture/module-boundaries-and-dependencies.md)
- [設定、執行與部署](../operations/configuration-and-deployment.md)
- [開發規則與測試策略](../operations/development-and-testing.md)
