---
type: development-guide
title: 開發規則與測試策略
description: 集中說明 Python 與 Nuxt 的程式碼分層、常用命令、測試邊界、CI 與提交前驗證。
tags: [development, testing, conventions, ci]
verified:
  - by: openwiki/0.6.0
    at: 2026-10-04T12:21:01.480Z
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
  - id: openwiki-source-4bb166095eacfb6386b2f861
    resource: repo://apps/whisper_summary/tests/integration/test_worker_task_leases.py
  - id: openwiki-source-16efc24ea6d42750c31dbc82
    resource: repo://apps/whisper_summary/tests/unit/test_discord_notifier.py
  - id: openwiki-source-d28dcebc0da3aee83d630395
    resource: repo://apps/whisper_summary/tests/unit/test_http_task_queue.py
  - id: openwiki-source-5d2812b91933bc74fcb0c6d9
    resource: repo://apps/whisper_summary/tests/unit/test_processing_engines.py
  - id: openwiki-source-f317ee207e1653d2033c81a4
    resource: repo://CONTRIBUTING.md
  - id: openwiki-source-012f2c78e3b1446dfc35803f
    resource: repo://Makefile
generated: { by: "codex", at: "2026-10-04T12:21:01.480Z" }
---

# 開發規則與測試策略

## 程式碼分層

- `apps/whisper_summary/domain/` 放 domain models 與 typed interfaces，不放第三方服務實作。
- `apps/whisper_summary/services/` 放 use case 與流程 orchestration。
- `apps/whisper_summary/infrastructure/` 放 LLM、媒體、通知、儲存與 SQLite/Notion adapters。
- `apps/whisper_summary/apps/` 是 FastAPI、Streamlit、CLI、RSS monitor 等執行入口；入口負責輸入輸出與 use case 組裝。
- `apps/showcase/` 是獨立的 Nuxt 3 展示站，使用自己的 TypeScript、Vue 與 Vitest 規則。

新增抽象放在 `apps/whisper_summary/domain/interfaces/`，新增 persistence adapter 放在 `apps/whisper_summary/infrastructure/persistence/`。主要行為應留在 service 層，不要把流程邏輯塞進 route 或 UI handler。

## 常用驗證

在 repository root 執行：

```bash
make test
make lint
npm --prefix apps/showcase run test
npm --prefix apps/showcase run build
```

Python 依賴使用 `uv sync --project apps/whisper_summary --frozen --no-install-project`；新增依賴後更新 `apps/whisper_summary/pyproject.toml` 與 `apps/whisper_summary/uv.lock`。第一次 checkout 執行 `make install-hooks`，提交前可用 `make betterleaks-staged` 驗證 staged secrets。

## 測試策略

Python 使用 `unittest` discovery；快速隔離測試放在 `apps/whisper_summary/tests/unit/`，跨 router、storage 或 UI seam 的測試放在 `apps/whisper_summary/tests/integration/`，Python 測試資料放在 `apps/whisper_summary/tests/fixtures/`；跨應用 contract fixture 放在 `contracts/`。LLM、Notion、Discord、yt-dlp 等網路或重型邊界使用 mock、fake 或 fixture。

Nuxt 使用 Vitest、Vue Test Utils 與 jsdom；測試放在 `apps/showcase/tests/`，命名為 `*.test.ts`。優先測試資料轉換、日期格式化、API handler、SWR cache 與 read state。

目前針對多 worker lease 的 API／SQLite 整合測試、HTTP queue adapter、legacy／LangGraph 引擎選擇，以及 Showcase 的同步驗證、設定與 Upstash 合併都有 focused tests。修改這些跨程序契約時，應先執行對應測試，再視變更範圍跑完整 CI 指令。

CI 有三個 jobs：Python執行 Flake8與 unittest，Showcase執行 npm test/build，Browser Extension執行 manifest/assets/JavaScript validator。Betterleaks 主要由本機 pre-commit hook執行。

### Discord 連結的隔離驗證

`test_discord_notifier.py` 使用 stub HTTP sender 驗證完整通知文字，涵蓋網站根網址清理、UUID 有無連字號、缺少或無效網址／ID、Notion 與知識庫連結同時存在，以及未設定 `NOTION_URL` 時仍產生知識庫連結；另保留 webhook 未設定、HTTP failure 與 request exception 的測試。

`test_processing_engines.py` 除了驗證兩個引擎的步驟順序、完成狀態與 notifier 參數，還在 Legacy 與 LangGraph 各執行一次實際的通知函式、只 stub HTTP post，確認最終 `/results/{id}` 指向 storage 回傳的摘要 UUID，且與完成狀態保存的 `notion_page_id` 相同。任務 ID 刻意使用不同值，避免把任務 ID 誤當摘要 ID。

```bash
PYTHONPATH=apps uv run --project apps/whisper_summary python -m unittest whisper_summary.tests.unit.test_discord_notifier whisper_summary.tests.unit.test_processing_engines whisper_summary.tests.unit.test_processing_engine_config -v
```

這些測試不發送真實 Discord 訊息，也不呼叫真實 Notion 或 LLM；網站範例使用 `knowledge.example.com`。本機 `.env` 或部署環境才保存實際網址，不將個人部署網址寫入測試、文件或 `.env.example`。正式網站的頁面存取與點擊仍需部署後驗收，不能由 stub 測試推定成功。

## Commit 與文件規則

Commit subject 使用簡短、現在式的 Conventional Commit 風格，例如 `fix: avoid duplicate task scheduling`。Pull Request 應包含摘要、動機、驗證結果與相關 issue；UI 變更另附畫面。

使用者可見的啟動或操作方式變更時，更新 `readme.md`；架構或流程變更時，透過 OpenWiki lifecycle 更新 generated wiki，不直接編輯 indexes、Claims 或 run metadata。功能需求與設計決策記錄在對應的 issue 或 Pull Request；持續有效的操作與開發規則同步更新正式文件。舊設計必須明確標示為歷史資料。

## 延伸閱讀

- [快速開始與開發導覽](../quickstart.md)
- [設定、執行與部署](configuration-and-deployment.md)
- [模組邊界與外部依賴](../architecture/module-boundaries-and-dependencies.md)
- [任務生命週期與併發控制](../workflows/task-lifecycle.md)
- [跨裝置已讀同步](../frontend/read-state-sync.md)
