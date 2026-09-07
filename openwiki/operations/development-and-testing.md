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
  - id: openwiki-source-f317ee207e1653d2033c81a4
    resource: repo://CONTRIBUTING.md
  - id: openwiki-source-012f2c78e3b1446dfc35803f
    resource: repo://Makefile
generated: { by: "codex", at: "2026-09-07T16:12:01.072Z" }
verified:
  - by: openwiki/0.4.3
    at: 2026-09-07T16:12:01.072Z
---

# 開發規則與測試策略

## 程式碼分層

- `src/domain/` 放 domain models 與 typed interfaces，不放第三方服務實作。
- `src/services/` 放 use case 與流程 orchestration。
- `src/infrastructure/` 放 LLM、媒體、通知、儲存與 SQLite/Notion adapters。
- `src/apps/` 是 FastAPI、Streamlit、CLI、RSS monitor 等執行入口；入口負責輸入輸出與 use case 組裝。
- `apps/showcase/` 是獨立的 Nuxt 3 展示站，使用自己的 TypeScript、Vue 與 Vitest 規則。

新增抽象放在 `src/domain/interfaces/`，新增 persistence adapter 放在 `src/infrastructure/persistence/`。主要行為應留在 service 層，不要把流程邏輯塞進 route 或 UI handler。

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

Python 使用 `unittest` discovery，測試檔放在 `tests/`，命名為 `test*.py`。優先覆蓋 task lifecycle、processing pipeline、URL validation、storage adapter 與 provider selection；LLM、Notion、Discord、yt-dlp 等網路或重型邊界使用 mock、fake 或 fixture，避免測試依賴外部服務。

Nuxt 使用 Vitest、Vue Test Utils 與 jsdom；測試放在 `apps/showcase/tests/`，命名為 `*.test.ts`。優先測試資料轉換、日期格式化、API handler、SWR cache 與 read state。

CI 的 Python gate 目前執行 flake8 與 unittest；Betterleaks 主要由本機 pre-commit hook 執行。文件或 UI 變更仍應選擇與風險相符的最小驗證，不要以未執行的測試宣稱完成。

## Commit 與文件規則

Commit subject 使用簡短、現在式的 Conventional Commit 風格，例如 `fix: avoid duplicate task scheduling`。Pull Request 應包含摘要、動機、驗證結果與相關 issue；UI 變更另附畫面。

使用者可見的啟動或操作方式變更時，更新 `readme.md`；架構或流程變更時，透過 OpenWiki lifecycle 更新 generated wiki，不直接編輯 indexes、Claims 或 run metadata。功能需求與設計決策放在 `openspec/`，舊設計必須明確標示為歷史資料。

## 延伸閱讀

- [快速開始與開發導覽](../quickstart.md)
- [設定、執行與部署](configuration-and-deployment.md)
- [模組邊界與外部依賴](../architecture/module-boundaries-and-dependencies.md)
<!-- openwiki: broken internal link [../testing/test-strategy.md] file "../testing/test-strategy.md" does not exist. Fix the href or restore the target, then delete this comment. -->
- [測試策略與擴充指南](../testing/test-strategy.md)
