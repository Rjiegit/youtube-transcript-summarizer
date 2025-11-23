# 專案資料夾結構（2025 重構後）

## 1. `src/` 主體分層
```
src/
  core/                   # 共用設定、log、工具
    config.py
    logger.py
    prompt.py
    utils/
      filename.py
      url.py
  domain/
    interfaces/           # DB、LLM、檔案等介面
      database.py
      file_manager_interface.py
      summarizer_interface.py
      summary_storage_interface.py
      transcriber_interface.py
    tasks/
      models.py           # Task dataclass 與欄位定義
  infrastructure/
    llm/summarizer_service.py
    media/
      downloader.py
      transcription/transcriber.py
    notifications/discord.py
    persistence/
      factory.py
      notion/{client.py, utils.py}
      sqlite/{client.py, task_adapter.py}
    storage/
      file_storage.py
      summary_storage.py
  services/
    outputs/path_builder.py        # 統一管理 summary 檔案命名
    pipeline/processing_runner.py  # ProcessingWorker 與 entry point
  apps/
    api/main.py
    ui/streamlit_app.py
    workers/cli.py
```

- `core`：集中環境設定 (`Config`)、logger、prompt 及 `filename/url` 工具，供 domain 與 infra 共用。
- `domain`：僅含型別與介面，`ProcessingWorker` 依賴 `BaseDB`、檔案/LLM 介面，讓測試與替換更容易。
- `infrastructure`：所有第三方實作（yt-dlp、Whisper、OpenAI/Gemini、Notion、Discord、檔案系統）皆置於此層。
- `services`：包裝 domain 流程與輸出工具；`processing_runner.ProcessPendingTasks` 注入 `downloader/transcriber/summarizer/summary_storage/file_manager` 工廠與 notifier。
- `apps`：不同入口點（FastAPI、Streamlit、CLI worker）只觸碰 service/API，不再直接 import infra。

## 2. Processing Pipeline 重構
- `ProcessingWorker` 會在初始化時注入：
  - `downloader_factory(url, output_path)`
  - `transcriber_factory(model_size)`
  - `summarizer_factory()`
  - `summary_storage_factory()`
  - `file_manager_factory()`
  - `notifier` 以及 `config_factory`
- 這些工廠預設使用 infra 層實作，但在 `tests/test_processing_worker.py` 中可直接 patch 或傳入客製工廠，減少廣域 `patch()`。
- Summary 檔名由 `services/outputs/path_builder.py` 管理，依據 timestamp + video id + sanitized title 產生 `data/summaries/` 內的路徑。

## 3. 相依模組
- 入口已全面改用 `src.*` 路徑，舊版 wrapper 已移除。
- `Makefile run` 執行 `python -m src.apps.workers.cli`，FastAPI 請用 `uvicorn src.apps.api.main:app`，Streamlit 請用 `streamlit run src/apps/ui/streamlit_app.py`。
- Document/README/GEMINI/AGENTS 已同步說明 `src/` 新位置；`structure.md` 即為最新參考。

## 4. 檔案搬移重點
- `database/*` 已拆為 `src/domain/interfaces`、`src/domain/tasks`、`src/infrastructure/persistence/...`
- `summarizer.py`、`summary_storage.py`、`transcriber.py`、`youtube_downloader.py`、`discord_notifier.py`、`file_manager.py` 已移至 infra 套件。
- `prompt.py` → `src/core/prompt.py`，供 summarizer backends 使用。

> 如需擴充新功能請將 domain/interface/service/infra 分層寫於 `src/`，避免再把新模組放在根目錄。新增入口點請放在 `src/apps/` 並視需要建立對應 wrapper。
