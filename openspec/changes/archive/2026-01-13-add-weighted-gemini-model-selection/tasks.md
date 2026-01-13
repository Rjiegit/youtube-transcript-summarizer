## 1. Implementation
- [ ] 新增 Gemini 加權模型清單（程式碼常數）與加權選模工具。
- [ ] 在 `Summarizer.summarize_with_google_gemini()` 實作加權隨機選模並更新 `last_model_label`。
- [ ] 保持未設定時沿用既有 `GEMINI_MODEL` 行為與輸出標籤格式。

## 2. Tests
- [ ] 新增單元測試：權重解析（合法/非法/空值）與選模（以可控 RNG 或 patch `random` 驗證）。

## 3. Docs
- [ ] 更新 README：說明 Gemini 加權模型目前為程式碼設定（以及調整權重的位置）。

## 4. Validation
- [ ] `python -m unittest -v`（或 `make test`）
- [ ] `flake8 .`
