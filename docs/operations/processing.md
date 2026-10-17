# Processing engine 與多 Worker 操作

從 repository 根目錄執行以下指令。

## Engine 切換

processing pipeline 支援兩個具有相同外部行為的 orchestration engine：

- `legacy`：既有循序流程，也是未設定時的安全預設。
- `langgraph`：以 LangGraph `StateGraph` 執行相同的下載、轉錄、摘要、儲存與通知步驟。

在 `apps/whisper_summary/.env` 設定全域預設，變更後重啟 processing worker：

```bash
PROCESSING_ENGINE=legacy
# 驗證完成後可改為：PROCESSING_ENGINE=langgraph
```

Streamlit 建立任務時也可選擇 `Legacy` 或 `LangGraph` 覆寫單筆任務；選擇
`Follow system default` 則使用 worker 的環境變數。API client 可在 `POST /tasks`
加入 `"processing_engine": "legacy"` 或 `"langgraph"`。回退時將環境變數改回
`legacy` 即可，已明確指定 engine 的待處理任務仍以任務設定優先。

SQLite 會自動新增 `processing_engine` 欄位。若 Notion task backend 需要使用單筆
覆寫，請先在 task database 建立名為 `Processing Engine` 的 Select property，選項為
`Legacy` 與 `LangGraph`；未設定單筆覆寫的既有頁面仍使用全域預設。

## 多 Worker 啟動與故障處置

Processing API 是 task lease 的中央協調者。Docker 與本機 worker 可以同時運行；每個
worker 一次處理一筆任務，而同一筆任務只會由一個 lease owner 取得。

先在 `apps/whisper_summary/.env` 設定 worker token（未設定時暫時相容
`PROCESSING_LOCK_ADMIN_TOKEN`）：

```env
PROCESSING_WORKER_TOKEN=<random-secret>
```

Docker worker 使用 Compose 內部 API URL：

```bash
docker compose up -d api streamlit rss-monitor processing-worker
```

本機 worker 使用 `TASK_API_BASE_URL`（預設 `http://localhost:8080`），並能使用主機上的
Codex CLI：

```bash
make processing-worker
```

兩者會以唯一 instance ID 競爭任務。Worker 以 heartbeat 維持 lease；lease 過期時任務
會直接標記為 `Failed`，不會自動交給另一個 worker 重跑。確認舊 worker 已停止後，可透過
既有 retry 操作建立新任務。Streamlit 的 `Processing Leases` 維運區可查看及手動標記
active lease 為 Failed。

## 實作導覽

Engine 的共用流程見 [媒體處理](../../openwiki/workflows/media-processing.md)；lease、heartbeat 與狀態轉移見 [任務生命週期](../../openwiki/workflows/task-lifecycle.md)。本頁維護操作步驟，內部機制與測試證據由 OpenWiki 說明。
