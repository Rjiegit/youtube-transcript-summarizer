# Quickstart: UI 列表顯示 Notion URL

1) **準備環境**
- 確認 `.env` 已設定 Notion 相關變數（若需同步 Notion）。
- 安裝依賴與工具：`make install`

2) **啟動後端與 UI**
- Docker: `docker compose up -d`
- Streamlit（本機）：`make streamlit` 或 `streamlit run src/apps/ui/streamlit_app.py`

3) **驗證功能**
- 造訪 UI 列表頁，檢查：
  - 有 Notion URL 的紀錄顯示可點擊連結並開啟正確頁面。
  - 無 Notion URL 的紀錄顯示提示文字，無空白或死鏈接。
  - 既有排序/搜尋/分頁仍正常。
- 若顯示「Notion 未設定」，請確認 `.env` 內 `NOTION_URL`/`NOTION_API_KEY`/`NOTION_DATABASE_ID` 是否正確。

4) **測試**
- 執行：`make test`
- 確認新增/更新的測試涵蓋：有 URL、缺漏、格式錯誤、頁面不存在（mock）。

5) **故障排除**
- 若 Notion URL 未顯示：檢查 API 回傳是否含 `notion_url` 欄位。
- 若載入變慢：檢查是否引入額外 Notion 呼叫，確保僅渲染現有欄位。
