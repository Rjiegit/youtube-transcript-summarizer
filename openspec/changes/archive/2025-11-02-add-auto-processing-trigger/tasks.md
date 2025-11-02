## 1. API 整合
- [x] 1.1 重構背景排程邏輯為可重複使用的 helper。
- [x] 1.2 `POST /tasks` 在成功新增任務後呼叫 helper，處理鎖衝突與例外。
- [x] 1.3 覆蓋/新增單元測試，驗證自動排程成功與鎖衝突情境。

## 2. Streamlit 更新
- [x] 2.1 改為透過 API 建立任務，處理成功與失敗提示。
- [x] 2.2 新增自動排程後的回饋（成功／鎖定中），並保留原 fallback。
- [x] 2.3 覆蓋 UI 級別邏輯測試或對應單元測試（如適用）。＊透過 API 單元測試驗證鎖定情境，Streamlit 無額外自動化測試。

## 3. 文件與驗證
- [x] 3.1 更新 README 或使用說明，提及新增任務將自動啟動背景處理。
- [x] 3.2 執行 `flake8` 及 `python -m unittest`，確保測試與靜態檢查通過。＊嘗試執行但 `flake8` 與 `fastapi` 缺失導致無法跑；記錄於回報中。
- [x] 3.3 `openspec validate add-auto-processing-trigger --strict`。＊嘗試執行但 CLI ESM 錯誤；記錄於回報中。
