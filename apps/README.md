# Applications

本目錄長期用來放置可獨立啟動、部署或發布的應用程式，不以程式語言或 UI／backend 類型區分。

## 目前內容

- [`browser-extension/`](browser-extension/)：Chrome／Edge Manifest V3 client，透過 HTTP 呼叫 FastAPI。
- [`showcase/`](showcase/)：Nuxt 3/Nitro 成果展示站，server routes 直接讀取 Notion。

## 現階段保留位置

目前只完成 Browser Extension 搬移。以下應用維持原路徑，等後續另行安排，不在本階段搬移：

- FastAPI：`src/apps/api/`。
- Streamlit operator UI：`src/apps/ui/`。
- Processing worker 與 RSS monitor：`src/apps/workers/`。

## 長期規劃

若後續執行完整的 application boundary 整理，候選結構如下：

```text
apps/
├─ api/
├─ operator-ui/
├─ processing-worker/
├─ rss-monitor/
├─ showcase/
└─ browser-extension/
```

`apps/` 只保存各應用專屬的 entrypoint、transport、UI 與 runtime configuration；共用 domain、application service 與 infrastructure adapter 應留在 Python 共用 package，避免在各應用間複製。

這是已記錄的長期方向，不代表上述目錄已建立或已排定搬移。
