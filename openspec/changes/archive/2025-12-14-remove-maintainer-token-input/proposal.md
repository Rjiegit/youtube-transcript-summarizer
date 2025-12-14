## Why
目前 Streamlit 維運區仍要求手動輸入 `X-Maintainer-Token`，但此工具僅供後台自用，應直接套用環境變數免去操作負擔並避免露出欄位。

## What Changes
- 移除 Processing Lock 維運區的 `X-Maintainer-Token` 輸入欄位，改由後端從設定取得並自動附加 header。
- 若缺少設定，介面需提示缺少維運 token。
- 更新相關文件說明改為自動取用配置。

## Impact
- Affected specs: processing-lock-admin
- Affected code: src/apps/ui/streamlit_app.py, readme.md
