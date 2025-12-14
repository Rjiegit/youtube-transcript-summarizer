## ADDED Requirements
### Requirement: Processing Lock Admin Token Is Preconfigured
Processing lock 維運操作 MUST 直接使用環境變數 `PROCESSING_LOCK_ADMIN_TOKEN` 設定的值作為 `X-Maintainer-Token`，不應要求介面使用者手動輸入。

#### Scenario: UI uses configured token automatically
- **GIVEN** Streamlit 維運區可取得 `PROCESSING_LOCK_ADMIN_TOKEN`
- **WHEN** 觸發查詢或釋放 processing lock
- **THEN** UI MUST 自動附帶 `X-Maintainer-Token` header 並不顯示手動輸入欄位

#### Scenario: Missing token blocks maintainer calls
- **GIVEN** 維運介面啟動時無法取得 `PROCESSING_LOCK_ADMIN_TOKEN`
- **WHEN** 使用者嘗試查詢或釋放 processing lock
- **THEN** UI MUST 顯示缺少維運 token 的警告並 MUST NOT 送出請求
