# Change: 新增瀏覽器外掛一鍵送出 YouTube 影片摘要任務

## Why
使用者目前需要手動複製 YouTube 影片網址貼到應用程式，流程繁瑣。透過瀏覽器外掛可直接在影片頁或列表連結一鍵送出任務，降低操作成本。

## What Changes
- 新增 Chrome/Edge (Manifest V3) 外掛，包含工具列按鈕與右鍵選單（影片頁與連結）送出任務
- 外掛提供 Options 頁，讓使用者設定後端 API Base URL
- 外掛在送出成功/失敗時顯示通知
- README 補充外掛安裝與設定步驟

## Impact
- Affected specs: browser-extension
- Affected code: src/apps/extension/, README
