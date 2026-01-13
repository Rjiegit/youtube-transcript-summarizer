# Change: Add weighted Gemini model selection

## Why
目前摘要固定使用 `gemini-2.5-flash`，容易遇到 rate limit，導致任務失敗率偏高。

## What Changes
- 新增「多個 Gemini model + 權重」的機制（於程式碼中定義），摘要時依權重加權隨機挑選模型。
- 保持向下相容：若權重清單為空或無效，維持既有 `GEMINI_MODEL` 行為。
- 既有 `model_label` 紀錄會改為反映實際選到的 Gemini model（用於 Notion/Markdown/DB 標記）。

## Non-Goals
- 不在此變更中新增「遇到 429/ResourceExhausted 自動換模型重試」邏輯（可另開變更）。
- 不改動 OpenAI/Ollama 的模型選擇策略。

## Impact
- Affected code (expected): `src/infrastructure/llm/summarizer_service.py`, `src/infrastructure/llm/model_options.py`。
- Affected behaviour: Gemini 摘要的模型不再固定；每次呼叫可能不同。

## Configuration
- 於 `src/infrastructure/llm/model_options.py` 定義 `GEMINI_WEIGHTED_MODELS`（code constant）。
