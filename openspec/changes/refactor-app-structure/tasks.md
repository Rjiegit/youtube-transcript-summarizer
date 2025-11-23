## 1. 建立 Src 與 Core/Domain 基礎
- [x] 1.1 新增 `src/` 目錄，搬移 `config.py`、`logger.py`、`url_validator.py`、`file_manager` 純工具至 `core`/`domain`.
- [x] 1.2 重構 `database/task.py` 與相關 dataclass 至 `domain/tasks/models.py`，維護型別與欄位一致。
- [x] 1.3 建立 `domain/interfaces/`，搬移現有 interface 並調整 import 以符合新套件路徑。

## 2. Processing Service / Pipeline
- [x] 2.1 將 `ProcessingWorker`、`ProcessingSummary`、鎖 refresher 與 `process_pending_tasks` 重構為 `services/pipeline/processing_runner.py`，並改用依賴注入。
- [x] 2.2 建立 `services/outputs/path_builder.py` 與 `core/utils/filename.py` 等 helper，替代原 `build_summary_output_path` 與 `FileManager` 耦合。
- [x] 2.3 更新 `tests/test_processing_worker.py` 與相關單元測試，使其使用新 service 與注入的 mock 介面。

## 3. Infrastructure Adapters
- [x] 3.1 建立 `infrastructure/media/downloader.py`、`infrastructure/media/transcription/faster_whisper.py`，並注入所需設定。
- [x] 3.2 拆分 `summarizer.py` 為 orchestrator + `llm/backends`，新增 mock/backends 的 interface 實作。
- [x] 3.3 將 `summary_storage.py`、`discord_notifier.py`、`file_manager.py` 等轉為 infrastructure adapter（Notion、Discord、檔案輸出），並確保符合 interface。

## 4. Apps 與設定更新
- [x] 4.1 搬移 FastAPI app 至 `apps/api/main.py` 並更新 import/依賴。
- [x] 4.2 將 `streamlit_app.py` 移至 `apps/ui/`，調整路徑與 CLI/Makefile/compose entry。
- [x] 4.3 新增 `apps/workers/cli.py` 或等效入口供 `make run`/Docker worker 使用，確保 pipeline 可被呼叫。

## 5. 文件與驗證
- [x] 5.1 更新 README、`structure.md`、開發指南以描述新目錄與指令。
- [x] 5.2 更新 `requirements.txt`、`setup.cfg`/`pyproject`（若需要）以支援新套件路徑。
- [x] 5.3 執行並紀錄 `flake8` 與 `python -m unittest -v` 結果，確保重構後仍通過。
