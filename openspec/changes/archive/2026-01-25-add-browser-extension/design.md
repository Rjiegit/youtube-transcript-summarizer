## Context
- 目標是在 YouTube 影片頁或列表中一鍵送出任務到既有 FastAPI `/tasks`。
- 外掛以 Chrome/Edge Manifest V3 實作，需透過 Options 頁設定 API Base URL。
- 請求由 extension service worker 發送，以避免頁面上下文的 CORS 限制。

## Goals / Non-Goals
- Goals:
  - 提供 action 按鈕與右鍵選單（頁面與連結）觸發任務
  - 提供 Options 頁設定 API Base URL
  - 送出後顯示成功/失敗通知
- Non-Goals:
  - 外掛內部顯示摘要結果或任務歷史
  - 外掛管理 Notion 或多帳號設定

## Decisions
- Decision: 使用 service worker (MV3) 作為背景邏輯，統一處理 action/context menu/送出流程並由其發送 API 請求。
- Decision: Options 頁以 `chrome.storage.sync` 保存 API Base URL，預設值為 `http://localhost:8080`。
- Decision: 對 `/tasks` 使用 payload `{ url, db_type: "sqlite" }`，保持最小化。

## Alternatives considered
- 只支援頁面 action，不做 context menu：流程較少，但不符合列表連結的使用情境。
- 不做 Options 頁，固定 localhost：不利於部署在不同環境或容器。

## Risks / Trade-offs
- Extension MV3 service worker 有生命週期限制，需要在每次事件內完成請求。

## Migration Plan
- 無資料遷移。

## Open Questions
- None.
