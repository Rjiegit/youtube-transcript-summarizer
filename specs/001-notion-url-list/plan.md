# Implementation Plan: UI 列表顯示 Notion URL

**Branch**: `001-notion-url-list` | **Date**: 2025-11-29 | **Spec**: specs/001-notion-url-list/spec.md
**Input**: Feature specification from `/specs/001-notion-url-list/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

在 Streamlit UI 的處理紀錄/摘要列表中顯示 Notion URL 欄位：有 URL 時顯示可點擊連結並跳轉正確頁面，缺漏或整合停用時顯示明確提示，不影響既有排序/搜尋/分頁與載入時間。

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11  
**Primary Dependencies**: Streamlit, FastAPI backend responses consumed by UI, Notion storage integration (existing), requests/HTTP client for API data  
**Storage**: 檔案輸出 (Markdown summaries) + Notion（已有 URL 來源）；無新增持久層  
**Testing**: unittest (`make test`), 可用 Streamlit 元件邏輯拆出函式做單元測試；外部呼叫以 mock 隔離  
**Target Platform**: Docker 服務與本機開發（macOS/Linux）  
**Project Type**: web（單一後端 + Streamlit 前端）  
**Performance Goals**: 列表載入時間增量 < 500ms；顯示新增欄位不影響既有排序/搜尋/分頁  
**Constraints**: PEP 8、行長 127；環境變數提供 Notion 設定；不得引入額外重量依賴  
**Scale/Scope**: 單 UI 列表畫面、現有任務量級；不更動資料模型僅讀現有 URL 欄位

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- 極簡與乾淨程式碼：僅在現有 Streamlit 列表中新增欄位與提示，不增新框架或抽象；維持單一責任與清晰命名。
- 代碼品質：實作後跑 `flake8 .`；所有 Notion/HTTP 互動以注入資料或 mock；配置仍走 `.env`。
- 測試標準：為有/無/錯誤 Notion URL 撰寫單元/整合測試並 mock 外部；`make test` 必跑。
- 使用者體驗一致性：訊息格式與既有 UI 一致，錯誤/缺漏時有明確提示，不破壞排序/搜尋/分頁。
- 效能目標：列表載入新增欄位增量 < 500ms；不重複呼叫 Notion；資料來源沿用後端回傳。

GATE 評估：目前無違規，准許進入 Phase 0。

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── apps/
│   ├── ui/streamlit_app.py
│   └── api/
├── infrastructure/
│   ├── storage/
│   ├── media/
│   └── llm/
├── services/
└── core/

tests/
├── unit/
└── integration/


**Structure Decision**: 採單一專案結構，UI 位於 `src/apps/ui/streamlit_app.py`，資料來源由現有後端/儲存層提供，測試放於 `tests/unit` 或 `tests/integration`。

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
