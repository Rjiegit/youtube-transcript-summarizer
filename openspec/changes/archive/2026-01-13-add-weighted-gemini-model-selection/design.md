# Design: Weighted Gemini model selection

## Overview
在 Gemini backend 使用前，根據程式碼中定義的加權模型清單進行加權隨機選模，並將實際使用的 model id 寫入 `Summarizer.last_model_label`，以便 `processing_runner` 組合 `model_label` 做儲存與追蹤。

## Configuration
- 於 `src/infrastructure/llm/model_options.py` 定義 `GEMINI_WEIGHTED_MODELS: list[WeightedModel]`。
- `model` 視為不透明字串，直接傳給 `genai.GenerativeModel(model)`.
- `weight` 為正整數；清單為空（或總權重不為正）時會回退到 `GEMINI_MODEL`。

## Selection algorithm
- 將解析後的清單展開為 `[(model, weight), ...]`，用加權隨機選擇：
  - 計算總權重 `W`
  - 取 `r = random.uniform(0, W)`
  - 依序累加權重，第一個使累加 >= r 的 model 為結果
- 若清單為空或解析後無有效項目，回退到既有常數 `GEMINI_MODEL`。

## Error handling
若權重清單為空或無效（總權重不為正），回退到預設模型 `GEMINI_MODEL`。

## Testing approach
- 抽出純函式：`choose_weighted_model(models_with_weights, rng=random) -> str`
- 以注入 RNG 或 patch `random.random` 方式做 determinism 測試，避免依賴統計分布。
