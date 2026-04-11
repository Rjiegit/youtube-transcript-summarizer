# Repository Guidelines

## Project Structure & Module Organization
本專案是 Nuxt 3 的展示頁應用。路由頁面放在 `pages/`（例如 `pages/index.vue`、`pages/results/[id].vue`），共用 UI 元件在 `components/`，可重用邏輯放在 `composables/`、`utils/` 與 `types/`。Server 端 API 與整合程式位於 `server/api/showcase/` 和 `server/utils/`。測試集中在 `tests/`，整合型測試用的固定資料放在 `test-data/`。全域樣式位於 `assets/css/main.css`，環境檢查等輔助腳本則放在 `scripts/`。

## Build, Test, and Development Commands
- `npm install`：安裝相依套件。
- `npm run dev`：啟動本機 Nuxt 開發伺服器，使用 `3000` port。
- `npm run build`：建立 production build。
- `npm run preview`：在本機預覽 build 後的結果。
- `npm run test`：執行一次 Vitest 測試。
- `npm run check-env`：檢查 showcase 所需的環境變數是否存在。

請在專案根目錄 `frontend/nuxt-showcase/` 下執行以上指令。

## Coding Style & Naming Conventions
請一致使用 TypeScript 與 Vue Single File Components。遵循既有風格：`.ts` 與 `.vue` 使用 2 spaces 縮排，變數與函式採 `camelCase`，元件採 `PascalCase`，檔名則延續既有慣例，不任意改寫命名風格（例如 `ShowcaseCard.vue`、`useReadResults.ts`）。Server 端工具函式應維持單一職責；格式化或資料轉換邏輯優先抽成 `utils/` 內的小型純函式。

## Testing Guidelines
測試使用 `Vitest`、`@vue/test-utils` 與 `jsdom`。新增測試請放在 `tests/`，命名採 `*.test.ts`。優先撰寫快速的單元測試，涵蓋日期格式化、資料轉換、快取行為與 API handler。大型測試資料請重用 `test-data/` 內的 fixtures，避免在測試中硬編大量 payload。提交 PR 前請先執行 `npm run test`。

## Commit & Pull Request Guidelines
近期提交紀錄採簡潔的 Conventional Commit 風格，例如 `feat: add datetime formatting utilities`。commit subject 請使用現在式，並聚焦單一變更。PR 內容應包含簡短摘要、相關 issue 或任務連結（若有）、測試證據，以及 UI 變更的畫面截圖。

## Security & Configuration Tips
不要提交任何 secret。Notion 存取設定請透過環境變數提供，例如 `NOTION_API_KEY`、`NOTION_DATABASE_ID`，以及選填的 `NOTION_STATUS_PROPERTY`。可使用 `/api/showcase/diagnostics` 與 `/api/showcase/health` 驗證執行時設定是否正確，同時避免暴露實際 secret 值。
