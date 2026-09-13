---
type: architecture
title: 模組邊界與外部依賴
description: 說明 Python modular monolith、獨立應用、composition roots，以及各 runtime 的依賴管理方式。
tags: [architecture, dependencies, python, boundaries]
verified:
  - by: openwiki/0.4.3
    at: 2026-09-13T10:51:33.281Z
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
  - id: openwiki-source-f317ee207e1653d2033c81a4
    resource: repo://CONTRIBUTING.md
  - id: openwiki-source-012f2c78e3b1446dfc35803f
    resource: repo://Makefile
  - id: openwiki-source-05ccef8d4cf1698187f20464
    resource: repo://pyproject.toml
  - id: openwiki-source-da418bc01cba89686ece3492
    resource: repo://scripts/install-git-hooks.sh
  - id: openwiki-source-1eb6a61d042052ba1402c2eb
    resource: repo://uv.lock
  - id: openwiki-source-ea52e4ece41ed31f8a8e2718
    resource: repo://whisper_summary/apps/api/schemas.py
  - id: openwiki-source-7286e0aae9c6fda5397f76b6
    resource: repo://whisper_summary/infrastructure/composition.py
  - id: openwiki-source-aa9bed27f533a96ebf77433d
    resource: repo://whisper_summary/infrastructure/media/downloader.py
  - id: openwiki-source-a5341de1a1a4430b8712b3f3
    resource: repo://whisper_summary/infrastructure/media/transcription/transcriber.py
  - id: openwiki-source-1b0a5fd67d6b13b8a3a3c17e
    resource: repo://whisper_summary/services/pipeline/dependencies.py
  - id: openwiki-source-aaaf86d61afa929bb997ee28
    resource: repo://whisper_summary/services/pipeline/processing_runner.py
generated: { by: "codex", at: "2026-09-13T10:51:33.281Z" }
---

# 模組邊界與外部依賴

Python 主系統是 `whisper_summary` package：`apps` 放 FastAPI、Streamlit、CLI 與常駐 worker 入口，`services` 負責 use case 與流程協調，`domain` 保存 models、interfaces 與 repository ports，`infrastructure` 實作 SQLite、Notion、media、LLM、storage 與 notification adapters。頂層 `apps/` 則保存不進入 Python import graph 的 Browser Extension 與 Nuxt Showcase。

## 組裝與依賴方向

Application service 依賴 domain contracts。資料庫與 RSS repository 由 `infrastructure/repository_composition.py` 建立；processing pipeline 的 downloader、transcriber、summarizer、storage、file manager、notifier 與 config factories 集中在 `infrastructure/composition.py`，再以 `ProcessingDependencies` 注入 `ProcessingWorker`。個別 factory 仍可由測試覆寫。

FastAPI 以 feature routers 組裝 HTTP surface；Streamlit、同步 CLI、processing worker 與 RSS monitor 各有獨立 entrypoint。Nuxt Showcase 的 server routes 直接讀取 Notion，Browser Extension 則以 HTTP 呼叫 FastAPI，因此兩者不 import Python implementation。

## Runtime dependencies

`pyproject.toml` 將 Python 依賴分成 `api`、`ui`、`worker` 與 `dev` groups；本機預設安裝全部 groups，Docker targets 則只安裝各自需要的 group。Nuxt 使用自己的 `package.json` 與 lockfile。`yt-dlp` 是 downloader 透過 subprocess 呼叫的外部 executable，由 Makefile／Docker 流程安裝，與 Python dependency resolution 分開。

轉錄 adapter 的預設路徑使用 `faster_whisper.WhisperModel`，同時保留 `whisper.load_model` 的 legacy method。API schema 直接使用 Pydantic，而 Pydantic 目前由 FastAPI dependency 帶入；若未來要獨立使用 schemas，應考慮升格為 direct API dependency。

## 驗證邊界

Python CI 安裝 lockfile、執行 Flake8 與 unittest；Showcase job 執行 npm test/build；Browser Extension job 驗證 manifest、assets 與 JavaScript。Betterleaks 則由 repository-local pre-commit hook 掃描 staged index，目前不在 GitHub Actions 中執行。

相關閱讀：[系統架構](system-overview.md)、[開發與測試](../operations/development-and-testing.md)。
