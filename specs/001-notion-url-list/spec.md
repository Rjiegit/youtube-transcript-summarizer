# Feature Specification: UI 列表顯示 Notion URL

**Feature Branch**: `001-notion-url-list`  
**Created**: 2025-11-29  
**Status**: Draft  
**Input**: User description: "讓 UI 的列表可以有 notion 的 url"
**Constitution Link**: 應對照 `.specify/memory/constitution.md`：保持最小可行變更、清晰命名、測試覆蓋、UX 一致性與效能目標。

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
  
  Assign priorities (P1, P2, P3, etc.) to each story, where P1 is the most critical.
  Think of each story as a standalone slice of functionality that can be:
  - Developed independently
  - Tested independently
  - Deployed independently
  - Demonstrated to users independently

  測試須列出單元/整合層級與 mock 策略（LLM、yt-dlp、Notion 等外部呼叫需隔離），並說明 CLI/API/Streamlit 的訊息/錯誤格式如何保持一致。
-->

### User Story 1 - 以 Notion 連結查看處理紀錄 (Priority: P1)

使用者在 UI 的處理紀錄/摘要列表中看到每筆紀錄的 Notion URL，點擊即可於瀏覽器開啟對應頁面。

**Why this priority**: 直接提供來源頁面，降低往返 Notion 查詢的時間並改善追蹤。

**Independent Test**: 造訪 UI 列表，確認具有 Notion URL 的紀錄皆顯示為可點擊連結且開啟正確頁面。

**Acceptance Scenarios**:

1. **Given** 列表存在帶有 Notion URL 的紀錄，**When** 使用者查看列表，**Then** 每筆紀錄顯示可點擊的 Notion URL 並跳轉至正確頁面。
2. **Given** Notion URL 存在但格式錯誤，**When** 使用者點擊連結，**Then** UI 顯示明確錯誤訊息並不破壞其他列的顯示。

---

### User Story 2 - 缺少 Notion 連結的清晰提示 (Priority: P2)

當紀錄沒有 Notion URL（未同步或 Notion 整合停用）時，使用者能在列表中看到明確標示與引導，不會誤認為資料遺失。

**Why this priority**: 降低疑惑與支持成本，明確告知缺漏原因或後續動作。

**Independent Test**: 造訪 UI 列表，確認沒有 Notion URL 的紀錄顯示一致的替代訊息，且不影響其他欄位。

**Acceptance Scenarios**:

1. **Given** Notion 整合已停用或紀錄尚未同步至 Notion，**When** 列表顯示該筆紀錄，**Then** 顯示標示（例如「尚未同步到 Notion」）且不呈現空白或死鏈接。

---

### User Story 3 - 檢索與排序仍保持一致 (Priority: P3)

當列表加入 Notion URL 資訊後，使用者仍可正常依現有欄位排序或搜尋，不會因新欄位破壞既有操作體驗。

**Why this priority**: 確保介面一致性與可用性，避免新增欄位造成既有功能退化。

**Independent Test**: 在列表中啟用排序或搜尋功能，確認結果與過往一致且 Notion URL 欄位正確顯示。

**Acceptance Scenarios**:

1. **Given** 列表支援排序/搜尋，**When** 使用者對其他欄位排序或搜尋，**Then** 新增的 Notion URL 欄位不影響結果且仍隨列一起顯示。

---

[Add more user stories as needed, each with an assigned priority]

### Edge Cases

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right edge cases.

  包含：外部服務不可用/超時、超大檔案或多任務併發、缺失環境變數/憑證、用戶輸入錯誤或缺漏。
-->

- Notion 整合未啟用或環境變數缺失時，列表如何顯示連結狀態。
- 紀錄存在但 Notion URL 為無效格式或已被刪除時，點擊後的行為與提示。
- 列表資料量大或載入緩慢時，Notion URL 欄位是否影響既有載入時間與可用性。

## Requirements *(mandatory)*

<!--
  ACTION REQUIRED: The content in this section represents placeholders.
  Fill them out with the right functional requirements.
-->

### Functional Requirements

- **FR-001**: 列表 MUST 顯示 Notion URL 欄位於每筆紀錄；當 URL 存在時需以可點擊連結呈現並指向正確頁面。
- **FR-002**: 列表 MUST 在 Notion URL 缺漏或 Notion 整合停用時，顯示一致且明確的替代訊息，不得顯示空白或無效連結。
- **FR-003**: 點擊 Notion URL 發生錯誤時（格式錯誤或頁面不存在），UI MUST 提供可理解的錯誤提示，不影響其他列操作。
- **FR-004**: 新增 Notion URL 欄位後，列表既有的排序/搜尋/分頁行為 MUST 保持功能正常且結果一致。
- **FR-005**: Notion URL 的來源資料 MUST 與後端存量一致（例如同一筆處理任務的 Notion URL），避免顯示過期或不符的連結。
- **FR-006**: Tests MUST cover happy path（有有效 Notion URL）與失敗情境（缺漏、停用、格式錯誤、頁面不存在），外部 Notion 呼叫需以 mock/fake 隔離；可由 `make test` 自動執行。
- **FR-007**: User-facing messages/errors MUST 遵循一致格式（含行為結果與後續指引），並在需要時提供可追蹤資訊（如任務 id 或檔名）。
- **FR-008**: Performance MUST 確保列表載入時間不因新增欄位而顯著增加；以現有資料量為基準，新增欄位後載入時間不得惡化超過可感知範圍（例如 < 500ms 增量），並需在測試中量測。

*Example of marking unclear requirements:*

- **FR-009**: System MUST authenticate users via [NEEDS CLARIFICATION: auth method not specified - email/password, SSO, OAuth?]
- **FR-010**: System MUST retain user data for [NEEDS CLARIFICATION: retention period not specified]

### Key Entities *(include if feature involves data)*

- **處理紀錄**: 單次影片處理或摘要紀錄，包含標題、建立時間、狀態、摘要路徑與可選的 Notion URL。
- **Notion 連結來源**: 儲存在處理紀錄中的 Notion 頁面 URL，可能因同步尚未完成或整合停用而缺漏。

## Assumptions

- 現有處理紀錄中已儲存（或可計算）Notion URL 欄位，無需改變資料模型即可讀取。
- Notion 整合可能被停用；此狀態可由現有設定或欄位判斷，不需額外存取 Notion 才能顯示。
- UI 列表沿用現有互動方式（排序、搜尋、分頁），新增欄位不改變既有操作入口。

## Success Criteria *(mandatory)*

<!--
  ACTION REQUIRED: Define measurable success criteria.
  These must be technology-agnostic and measurable.
-->

### Measurable Outcomes

- **SC-001**: 95% 以上有 Notion URL 的紀錄在列表中顯示正確連結並可成功開啟。
- **SC-002**: 缺少 Notion URL 的紀錄 100% 顯示一致的替代訊息，無空白或無效連結。
- **SC-003**: 列表新增 Notion URL 後的載入時間較目前增加不超過 500ms（以相同資料量測試）。
- **SC-004**: `make test` 全數通過，且新增/修改的測試涵蓋 Notion URL 存在、缺漏、格式錯誤與整合停用情境。
- **SC-005**: 使用者在 UX 驗收中能於 1 次操作內找到並開啟對應 Notion 頁面，無需額外查找或詢問。
