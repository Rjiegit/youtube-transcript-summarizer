# Tasks: UI 列表顯示 Notion URL

**Input**: Design documents from `specs/001-notion-url-list/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: 測試為必填交付品；每個行為的單元/整合測試須覆蓋主要成功與失敗路徑，並以 mock/fake 隔離外部服務（LLM、yt-dlp、Notion 等）。`make test` 需可直接執行。

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. 保持最小可行變更與清晰命名；避免不必要抽象或依賴。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions
- 若新增依賴或設定，需註明 `.env`/Makefile/Docker 變更與回滾方式。

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Validate Notion 相關環境變數與 `.env` 範例，補充需要的鍵名說明（.env.example）
- [X] T002 [P] 確認/安裝前端依賴並可啟動 Streamlit（`make install`、`make streamlit` 說明更新於 quickstart.md）

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 確認後端列表 API 回傳包含 `notion_url` 欄位並符合契約（specs/001-notion-url-list/contracts/listing.md）
- [X] T004 建立/更新後端測試 fixture 或 mock 資料，涵蓋有/無/錯誤的 `notion_url`（tests/fixtures/processing_jobs.py）
- [X] T005 驗證現有資料模型讀取 `notion_url` 不需遷移，記錄於研究/計畫（specs/001-notion-url-list/research.md）

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 以 Notion 連結查看處理紀錄 (Priority: P1) 🎯 MVP

**Goal**: 使用者在列表看到可點擊的 Notion URL 並能正確開啟

**Independent Test**: 造訪列表，帶有 URL 的紀錄皆顯示連結且成功跳轉；錯誤 URL 顯示提示不影響其他列

### Tests for User Story 1 (Mandatory) ⚠️

- [X] T006 [P] [US1] 單元測試：渲染有/無/錯誤 `notion_url` 的列表資料，檢查欄位與連結（tests/unit/test_streamlit_list_notion_url.py）
- [X] T007 [P] [US1] 整合測試：模擬 API 回傳含 `notion_url`，驗證 UI 端點/頁面顯示與跳轉結果（tests/integration/test_streamlit_list_notion_url.py）

### Implementation for User Story 1

- [X] T008 [US1] 在 Streamlit 列表新增「Notion」欄位與可點擊連結渲染，連結錯誤時顯示提示（src/apps/ui/streamlit_app.py）
- [X] T009 [P] [US1] 更新 UI 資料轉換/組裝邏輯，確保 `notion_url` 來源與後端一致（src/apps/ui/streamlit_app.py）
- [X] T010 [US1] 補充文件/說明：在 quickstart 中加入 Notion URL 驗證步驟（specs/001-notion-url-list/quickstart.md）

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - 缺少 Notion 連結的清晰提示 (Priority: P2)

**Goal**: 缺漏或停用 Notion 時，列表顯示一致且明確的替代訊息

**Independent Test**: 無 `notion_url` 的紀錄均顯示提示，不影響其他欄位與操作

### Tests for User Story 2 (Mandatory) ⚠️

- [X] T011 [P] [US2] 單元測試：`notion_url` 為 null/缺失/停用狀態時顯示提示字串（tests/unit/test_streamlit_list_missing_notion.py）
- [X] T012 [P] [US2] 整合測試：API 回傳缺漏/停用案例，UI 顯示提示且不中斷頁面（tests/integration/test_streamlit_list_notion_url.py）

### Implementation for User Story 2

- [X] T013 [US2] 在 UI 增加缺漏/停用的提示邏輯與文案，避免空白或死鏈接（src/apps/ui/streamlit_app.py）
- [X] T014 [P] [US2] 若需設定開關，文件化 Notion 整合停用時的行為與環境變數（quickstart.md）

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - 檢索與排序仍保持一致 (Priority: P3)

**Goal**: 新增欄位後，列表排序/搜尋/分頁仍維持既有行為

**Independent Test**: 啟用排序/搜尋後結果與既有一致，Notion 欄位隨列正確顯示

### Tests for User Story 3 (Mandatory) ⚠️

- [X] T015 [P] [US3] 單元/整合測試：排序/搜尋輸入後，Notion 欄位不破壞結果與顯示（tests/integration/test_streamlit_list_sort_search.py）

### Implementation for User Story 3

- [X] T016 [US3] 驗證並調整列表排序/搜尋流程，確保新增欄位不影響現有邏輯（src/apps/ui/streamlit_app.py）
- [X] T017 [P] [US3] 若需，更新 UI 層的資料欄位映射以配合排序/搜尋（src/apps/ui/streamlit_app.py）

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T018 [P] 更新相關文件（如 README/quickstart）摘要 Notion URL 欄位行為與測試命令（readme.md）
- [X] T019 碼整潔與重構：移除重複邏輯、維持單一責任（src/apps/ui/streamlit_app.py）
- [X] T020 性能檢查：記錄列表載入時間前後差異，確保增量 < 500ms（tests/integration/test_streamlit_list_performance.py）
- [X] T021 [P] 安全檢查：確認未曝光 Notion/機密資訊於 UI/日誌（src/apps/ui/streamlit_app.py）
- [ ] T022 執行 `flake8 .` 與 `make test` 並記錄結果於 PR 說明（repo root）

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → Polish
- User stories可在完成 Foundation 後依優先順序實作；US2/US3 可在 US1 完成後並行。

## Parallel Opportunities

- T002, T004 可並行（不同檔案與責任）。
- US1 測試 T006、T007 可並行；US2 測試 T011、T012 可並行。
- Polish 中 T018、T019、T021 可與性能量測 T020 分開執行。

## Implementation Strategy

- MVP：完成 US1（T006-T010）即可交付可用的 Notion 連結顯示。
- Incremental：US2 解決缺漏提示；US3 確保排序/搜尋一致性；最後執行 Polish 驗證與清理。
