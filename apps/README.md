# Applications

本目錄放置可獨立啟動、部署或發布的應用程式，不以程式語言或 UI／backend 類型區分。

## 目前內容

- [`whisper_summary/`](whisper_summary/)：Python package，包含 FastAPI、Streamlit、worker 入口及共用的 domain、services、infrastructure。
- [`browser-extension/`](browser-extension/)：Chrome／Edge Manifest V3 client，透過 HTTP 呼叫 FastAPI。
- [`showcase/`](showcase/)：Nuxt 3/Nitro 成果展示站，server routes 直接讀取 Notion。

Python package 的 import 名稱維持 `whisper_summary`。從 repository root 執行 Python 指令時，需將
`apps/` 放進 `PYTHONPATH`；Makefile、Docker image 與 CI 已設定。手動執行可使用
`PYTHONPATH=apps uv run python -m whisper_summary.apps.workers.cli`。
