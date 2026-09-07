# Browser Extension

Chrome／Edge Manifest V3 extension，用來從 YouTube 頁面送出影片摘要任務及建立 channel RSS subscription。

## 本機載入

1. 啟動 FastAPI：`make api`。
2. 開啟瀏覽器的 extension management 頁面並啟用 Developer mode。
3. 選擇 Load unpacked，載入 repository 的 `apps/browser-extension/`。
4. 在 extension options 設定 Task API base URL；本機預設為 `http://localhost:8080`。

## 整合邊界

- `service_worker.js` 呼叫 FastAPI 的 task 與 RSS endpoints。
- `content_script.js` 只從 YouTube DOM 讀取 channel context。
- API base URL 儲存在 `chrome.storage.sync`。
- 本目錄不屬於 Python `src/`，不應直接 import Python implementation。

## 修改後驗證

- 確認 `manifest.json` 可解析，且其中引用的 scripts、options page 與 icons 都存在。
- 對所有 JavaScript 檔案執行 `node --check`。
- 以 Load unpacked 重新載入後，手動驗證影片任務送出與 RSS subscription。
