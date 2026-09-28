---
type: development-guide
title: 開發規則與測試策略
description: 集中說明 Python 與 Nuxt 的程式碼分層、常用命令、測試邊界、CI 與提交前驗證。
tags: [development, testing, conventions, ci]
sources:
  - id: openwiki-source-bf5be0c9253ed1d07b502e10
    resource: repo://.githooks/pre-commit
  - id: openwiki-source-ee3ea3bd39689f7e4f5dc7c6
    resource: repo://.github/workflows/main.yml
  - id: openwiki-source-8037e2358a2c4f9b2c722a11
    resource: repo://AGENTS.md
  - id: openwiki-source-ec214e818e93e527ce43036b
    resource: repo://apps/showcase/AGENTS.md
  - id: openwiki-source-40202183da1fe23aacead855
    resource: repo://apps/showcase/tests/read-sync-auth.test.ts
  - id: openwiki-source-c4b4f6bb443d3d8efa5f9b95
    resource: repo://apps/showcase/tests/upstash-read-state.test.ts
  - id: openwiki-source-f317ee207e1653d2033c81a4
    resource: repo://CONTRIBUTING.md
  - id: openwiki-source-012f2c78e3b1446dfc35803f
    resource: repo://Makefile
  - id: openwiki-source-9398efacd8bb9280dd0ee0b5
    resource: repo://tests/integration/test_worker_task_leases.py
  - id: openwiki-source-e4dabfd80c2160d35bf96b4a
    resource: repo://tests/unit/test_http_task_queue.py
  - id: openwiki-source-bc6ea497842aa371304db838
    resource: repo://tests/unit/test_processing_engines.py
generated: { by: "codex", at: "2026-09-28T12:59:50.272Z" }
verified:
  - by: openwiki/0.4.3
    at: 2026-09-28T12:59:50.272Z
---

# 開發規則與測試策略

## 程式碼分層

- `whisper_summary/domain/` 放 domain models 與 typed interfaces，不放第三方服務實作。
- `whisper_summary/services/` 放 use case 與流程 orchestration。
- `whisper_summary/infrastructure/` 放 LLM、媒體、通知、儲存與 SQLite/Notion adapters。
- `whisper_summary/apps/` 是 FastAPI、Streamlit、CLI、RSS monitor 等執行入口；入口負責輸入輸出與 use case 組裝。
- `apps/showcase/` 是獨立的 Nuxt 3 展示站，使用自己的 TypeScript、Vue 與 Vitest 規則。

新增抽象放在 `whisper_summary/domain/interfaces/`，新增 persistence adapter 放在 `whisper_summary/infrastructure/persistence/`。主要行為應留在 service 層，不要把流程邏輯塞進 route 或 UI handler。

## 常用驗證

在 repository root 執行：

```bash
make test
uv run flake8 .
npm --prefix apps/showcase run test
npm --prefix apps/showcase run build
```

Python 依賴使用 `uv sync --frozen --no-install-project`；新增依賴後更新 `pyproject.toml` 與 `uv.lock`。第一次 checkout 執行 `make install-hooks`，提交前可用 `make betterleaks-staged` 驗證 staged secrets。

## 測試策略

Python 使用 `unittest` discovery；快速隔離測試放在 `tests/unit/`，跨 router、storage 或 UI seam 的測試放在 `tests/integration/`，共享 contract/data放在 `tests/fixtures/`。LLM、Notion、Discord、yt-dlp 等網路或重型邊界使用 mock、fake 或 fixture。

Nuxt 使用 Vitest、Vue Test Utils 與 jsdom；測試放在 `apps/showcase/tests/`，命名為 `*.test.ts`。優先測試資料轉換、日期格式化、API handler、SWR cache 與 read state。

目前針對多 worker lease 的 API／SQLite 整合測試、HTTP queue adapter、legacy／LangGraph 引擎選擇，以及 Showcase 的同步驗證、設定與 Upstash 合併都有 focused tests。修改這些跨程序契約時，應先執行對應測試，再視變更範圍跑完整 CI 指令。

CI 有三個 jobs：Python執行 Flake8與 unittest，Showcase執行 npm test/build，Browser Extension執行 manifest/assets/JavaScript validator。Betterleaks 主要由本機 pre-commit hook執行。

## Commit 與文件規則

Commit subject 使用簡短、現在式的 Conventional Commit 風格，例如 `fix: avoid duplicate task scheduling`。Pull Request 應包含摘要、動機、驗證結果與相關 issue；UI 變更另附畫面。

使用者可見的啟動或操作方式變更時，更新 `readme.md`；架構或流程變更時，透過 OpenWiki lifecycle 更新 generated wiki，不直接編輯 indexes、Claims 或 run metadata。功能需求與設計決策記錄在對應的 issue 或 Pull Request；持續有效的操作與開發規則同步更新正式文件。舊設計必須明確標示為歷史資料。

## 延伸閱讀

- [快速開始與開發導覽](../quickstart.md)
- [設定、執行與部署](configuration-and-deployment.md)
- [模組邊界與外部依賴](../architecture/module-boundaries-and-dependencies.md)
- [任務生命週期與併發控制](../workflows/task-lifecycle.md)
- [跨裝置已讀同步](../frontend/read-state-sync.md)
