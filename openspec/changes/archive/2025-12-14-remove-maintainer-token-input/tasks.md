## 1. Implementation
- [x] 1.1 移除 Streamlit Processing Lock 維運區的 token 輸入，統一從環境變數載入並附加 header。
- [x] 1.2 缺少維運 token 時在 UI 顯示提示並避免送出查詢/釋放請求。
- [x] 1.3 更新文件，說明維運介面自動使用設定的 token。

## 2. Validation
- [x] 2.1 `openspec validate remove-maintainer-token-input --strict`
