## Why
- 核心模組（特別是 `processing.py`）同時掌管 domain 流程、基礎設施、檔案系統與通知，導致 UI/API 入口緊耦合，難以擴充或測試。
- `summarizer`、`transcriber`、`summary_storage` 等模組直接依賴第三方 SDK 與 Streamlit session，缺少介面抽象，造成 background worker 與 CLI 也必須載入 UI 相關依賴。
- 目錄結構平坦且混合 domain/infrastructure/adapters，維護者難以辨識責任邊界，測試需要大量 patch，阻礙後續功能開發。

## What Changes
- 在 `src/` 底下建立 `core`/`domain`/`infrastructure`/`services`/`apps` 分層，移動現有模組並補齊封裝（詳見 `structure.md`）。
- 將 `ProcessingWorker` 與 `process_pending_tasks` 重構為 domain/service 層，透過介面注入 downloader、transcriber、summarizer、summary repository、notifier。
- 拆分 `summarizer` 與 `summary_storage` 使其成為 infrastructure adaptor，對接多種 backend 並隔離 Streamlit/TestSampleManager 判斷。
- 調整 FastAPI、Streamlit、CLI/docker entry 只呼叫 service 層，更新 Makefile/compose/README。
- 依新結構更新測試、imports、linter/config，確保 `flake8` 與 `unittest` 可在搬移後順利執行。

## Impact
- 大量檔案移動與 import 變更，需同步更新測試、CI、開發指令與 Docker 服務設定。
- 重構過程可能短暫破壞現有功能，需分階段提交並確保單元測試補齊；也需通知其他協作者暫停在舊目錄上開發。
- 之後新增功能可直接在對應層級介面中擴充，開發效率提升，但需要團隊熟悉新結構與依賴注入方式。
