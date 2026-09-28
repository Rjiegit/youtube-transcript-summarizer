---
type: architecture
title: 模組邊界與外部依賴
description: 說明 Python modular monolith、獨立應用、composition roots，以及各 runtime 的依賴管理方式。
tags: [architecture, dependencies, python, boundaries]
verified:
  - by: openwiki/0.4.3
    at: 2026-09-28T16:59:07.681Z
sources:
  - id: openwiki-source-269e1e25890c094aaa09d0a0
    resource: repo://.docker/Dockerfile
  - id: openwiki-source-bf5be0c9253ed1d07b502e10
    resource: repo://.githooks/pre-commit
  - id: openwiki-source-ee3ea3bd39689f7e4f5dc7c6
    resource: repo://.github/workflows/main.yml
  - id: openwiki-source-3f302af29bc8e91334af86aa
    resource: repo://apps/browser-extension/service_worker.js
  - id: openwiki-source-820d12d8c5440c6adcd393be
    resource: repo://apps/README.md
  - id: openwiki-source-bbc421d322d74564a269df19
    resource: repo://apps/showcase/package.json
  - id: openwiki-source-f987324e0612a557c62a85fb
    resource: repo://apps/showcase/server/api/showcase/results.get.ts
  - id: openwiki-source-8a8f27feb31a478f83017412
    resource: repo://apps/whisper_summary/apps/api/routers/processing.py
  - id: openwiki-source-e8a3e4e8f72c5329a78957ec
    resource: repo://apps/whisper_summary/apps/api/schemas.py
  - id: openwiki-source-cfa98d1a4968f26a13388580
    resource: repo://apps/whisper_summary/infrastructure/composition.py
  - id: openwiki-source-e3deef680a5ed6126a3e663d
    resource: repo://apps/whisper_summary/infrastructure/media/downloader.py
  - id: openwiki-source-b94cf9b6029f1843e044616d
    resource: repo://apps/whisper_summary/infrastructure/media/transcription/transcriber.py
  - id: openwiki-source-8a62d9c1de9e763d89cb9eb8
    resource: repo://apps/whisper_summary/infrastructure/task_queue/http_client.py
  - id: openwiki-source-44f784ddceb054f0c06a5950
    resource: repo://apps/whisper_summary/pyproject.toml
  - id: openwiki-source-4594a94ad039182278792218
    resource: repo://apps/whisper_summary/services/pipeline/dependencies.py
  - id: openwiki-source-79006d740abb2f90a0561607
    resource: repo://apps/whisper_summary/services/pipeline/engines.py
  - id: openwiki-source-9d74f9961da3fcb79187c2ef
    resource: repo://apps/whisper_summary/services/pipeline/langgraph_engine.py
  - id: openwiki-source-5d30f93453a5fc9227aa0b47
    resource: repo://apps/whisper_summary/services/pipeline/processing_runner.py
  - id: openwiki-source-33d6df1a99d77cb29ddb5342
    resource: repo://apps/whisper_summary/uv.lock
  - id: openwiki-source-f317ee207e1653d2033c81a4
    resource: repo://CONTRIBUTING.md
  - id: openwiki-source-012f2c78e3b1446dfc35803f
    resource: repo://Makefile
  - id: openwiki-source-da418bc01cba89686ece3492
    resource: repo://scripts/install-git-hooks.sh
generated: { by: "codex", at: "2026-09-28T16:59:07.681Z" }
---

# 模組邊界與外部依賴

Python 主系統位於 `apps/whisper_summary/`，import 名稱維持 `whisper_summary`：`apps` 放 FastAPI、Streamlit、CLI 與常駐 worker 入口，`services` 負責 use case 與流程協調，`domain` 保存 models、interfaces 與 repository ports，`infrastructure` 實作 SQLite、Notion、media、LLM、storage 與 notification adapters。頂層 `apps/` 同時收納 Python 主系統、獨立的 Browser Extension 與 Nuxt Showcase；後兩者不進入 Python import graph。

## 組裝與依賴方向

Application service 依賴 domain contracts。資料庫與 RSS repository 由 `infrastructure/repository_composition.py` 建立；processing pipeline 的 downloader、transcriber、summarizer、storage、file manager、notifier 與 config factories 集中在 `infrastructure/composition.py`，再以 `ProcessingDependencies` 注入 `ProcessingWorker`。個別 factory 仍可由測試覆寫。

Task queue 的 lease 操作定義在 `domain/ports/task_queue.py`；常駐 worker 透過 `infrastructure/task_queue/http_client.py` 呼叫中央 FastAPI queue。API 持有 SQLite backend，worker 可與 API 分開執行。兩種 processing engine 共用 `services/pipeline/engines.py` 的操作，`langgraph_engine.py` 只負責圖的順序編排。

FastAPI 以 feature routers 組裝 HTTP surface；Streamlit、同步 CLI、processing worker 與 RSS monitor 各有獨立 entrypoint。Nuxt Showcase 的 server routes 直接讀取 Notion，Browser Extension 則以 HTTP 呼叫 FastAPI，因此兩者不 import Python implementation。

## Runtime dependencies

`apps/whisper_summary/pyproject.toml` 將 Python 依賴分成 `api`、`ui`、`worker` 與 `dev` groups；本機預設安裝全部 groups，Docker targets 則只安裝各自需要的 group。Nuxt 使用自己的 `package.json` 與 lockfile。`yt-dlp` 是 downloader 透過 subprocess 呼叫的外部 executable，由 Makefile／Docker 流程安裝，與 Python dependency resolution 分開。

轉錄 adapter 的預設路徑使用 `faster_whisper.WhisperModel`，同時保留 `whisper.load_model` 的 legacy method。API schema 直接使用 Pydantic，而 Pydantic 目前由 FastAPI dependency 帶入；若未來要獨立使用 schemas，應考慮升格為 direct API dependency。Worker group 另包含 LangGraph，供選用的圖式 orchestration 使用。

## 驗證邊界

Python CI 從 `apps/whisper_summary/` 安裝 lockfile、執行 Flake8 與 unittest；Showcase job 執行 npm test/build；Browser Extension job 驗證 manifest、assets 與 JavaScript。Betterleaks 則由 repository-local pre-commit hook 掃描 staged index，目前不在 GitHub Actions 中執行。

Python 的 unit／integration 測試與 fixtures 放在 `apps/whisper_summary/tests/`；Nuxt 測試放在 `apps/showcase/tests/`，兩者共用的契約 fixture 保留在頂層 `contracts/`。

相關閱讀：[系統架構](system-overview.md)、[開發與測試](../operations/development-and-testing.md)。
