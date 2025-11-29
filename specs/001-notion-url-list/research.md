# Research: UI 列表顯示 Notion URL

## Decisions

- **資料來源**: 使用現有處理紀錄的 Notion URL 欄位（不改模型），由後端 API/資料層直接提供。
  - **Rationale**: 避免新增查詢與 I/O；保持最小變更。
  - **Alternatives considered**: 進入 UI 時即時呼叫 Notion 取得連結（放棄，增加延遲與外部依賴）。

- **呈現格式**: 在列表新增「Notion」欄位，存在時顯示可點擊 URL；缺漏時顯示固定提示（如「尚未同步到 Notion」）。
  - **Rationale**: 與既有欄位一致，降低使用者混淆。
  - **Alternatives considered**: 以 icon 取代文字（放棄，易造成可見性不足）。

- **錯誤處理**: URL 格式錯誤或已刪除時，顯示可理解的錯誤訊息，不影響其他列。
  - **Rationale**: 保持 UX 一致性並可追蹤問題。
  - **Alternatives considered**: 靜默失敗（放棄，降低可用性）。

- **效能策略**: 不新增額外 Notion 呼叫，僅渲染已存在的 URL；列表載入增量目標 < 500ms。
  - **Rationale**: 符合憲章「最小變更」與性能要求。
  - **Alternatives considered**: 每列懶加載 Notion 狀態（放棄，會增加外部依賴與延遲）。

- **測試策略**: 以 mock/fake 模擬 Notion URL 狀態（存在、缺漏、格式錯誤、頁面不存在），驗證渲染與訊息。
  - **Rationale**: 減少外部依賴，確保 `make test` 可離線執行。
  - **Alternatives considered**: 實際呼叫 Notion（放棄，成本高且不穩定）。

- **資料模型**: 不新增資料庫欄位，`notion_url` 由 `NOTION_URL` + `notion_page_id` 動態組合；SQLite 仍僅儲存 page id。
  - **Rationale**: 避免遷移，維持最小變更。
  - **Alternatives considered**: 新增欄位持久化完整 URL（放棄，需遷移且易過期）。
