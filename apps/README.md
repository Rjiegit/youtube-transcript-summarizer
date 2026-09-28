# Applications

本目錄放置可獨立啟動、部署或發布的應用程式，不以程式語言或 UI／backend 類型區分。

## 目前內容

- [`whisper_summary/`](whisper_summary/)：Python package，包含 FastAPI、Streamlit、worker 入口及共用的 domain、services、infrastructure。
- [`browser-extension/`](browser-extension/)：Chrome／Edge Manifest V3 client，透過 HTTP 呼叫 FastAPI。
- [`showcase/`](showcase/)：Nuxt 3/Nitro 成果展示站，server routes 直接讀取 Notion。

Python 專案的 `pyproject.toml`、`uv.lock`、`.env.example` 與 lint 設定都放在
`apps/whisper_summary/`；Showcase 使用自己的 `package.json` 與 `.env`。
Python package 的 import 名稱維持 `whisper_summary`。從 repository root 手動執行時，需指定
uv project 和 `PYTHONPATH`；Makefile、Docker image 與 CI 已設定。手動執行可使用
`PYTHONPATH=apps uv run --project apps/whisper_summary --env-file apps/whisper_summary/.env python -m whisper_summary.apps.workers.cli`。
