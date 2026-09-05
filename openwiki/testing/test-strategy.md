---
type: testing-guide
title: 測試策略與擴充指南
description: 說明 Python unittest 與 Nuxt Vitest 的風險分層、mock seams、關鍵 invariants 與執行方式。
tags: [testing, unittest, vitest, quality]
sources:
  - id: openwiki-source-ee3ea3bd39689f7e4f5dc7c6
    resource: repo://.github/workflows/main.yml
  - id: openwiki-source-fcc5a6911958eaf3419d651d
    resource: repo://frontend/nuxt-showcase/tests/showcase-index-page.test.ts
  - id: openwiki-source-6f3d5ab2255c7aff38623726
    resource: repo://frontend/nuxt-showcase/tests/swr-cache.test.ts
  - id: openwiki-source-0695e63141450a46a401af8f
    resource: repo://frontend/nuxt-showcase/vitest.config.ts
  - id: openwiki-source-012f2c78e3b1446dfc35803f
    resource: repo://Makefile
  - id: openwiki-source-15d018e604de3b705c66eb19
    resource: repo://tests/test_api_create_task.py
  - id: openwiki-source-839ded7442c98545a6825769
    resource: repo://tests/test_processing_worker.py
  - id: openwiki-source-7def47d9e5d7b25e40812c7c
    resource: repo://tests/test_summarizer_service.py
  - id: openwiki-source-e2ee026fbcf730652e2c0e63
    resource: repo://tests/test_weighted_selection.py
generated: { by: "codex", at: "2026-09-05T13:06:08.754Z" }
verified:
  - by: openwiki/0.4.3
    at: 2026-09-05T13:06:08.754Z
---

# 測試策略與擴充指南

本 repo 以快速、隔離的行為測試為主。Python 使用 `unittest`，Nuxt 使用 Vitest、Vue Test Utils 與 jsdom。提交前分別執行：

```bash
make test
npm --prefix frontend/nuxt-showcase run test
```

一般本機 lint 可執行 `uv run flake8 .`；若要重現 `.github/workflows/main.yml` 的 CI 行為，使用：

```bash
uv run flake8 . --exclude=.venv,.archive --count --select=E9,F63,F7,F82 --show-source --statistics
uv run flake8 . --exclude=.venv,.archive --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
uv run python -m unittest discover
```

第一段 lint 會阻擋指定的語法與名稱錯誤；第二段以 `--exit-zero` 回報其他問題，不會因 lint findings 使 CI 失敗。CI 的 unittest 使用預設 discovery；`make test` 則明確指定 root、`test*.py` 與 verbose 輸出。目前這份 workflow 不執行 Nuxt tests 或 production build，修改前端時需另行驗證。

## Python 風險層

- **API contract**：FastAPI TestClient 驗證 URL normalization、status code、dedup/cache policy、backend configuration、worker scheduling 與 lock admin authorization。外部 database 與 scheduler 應 mock，assert response 與 collaborator calls。
- **Queue/persistence invariants**：SQLite tests 使用暫存 database 驗證 migrations、task status、locks、retry relationship、recent history 與 RSS watermark。這一層保留真實 SQL，mock network。
- **Processing orchestration**：worker tests 替換 downloader、transcriber、summarizer、file/Notion storage、notification 與 config，驗證呼叫順序的可觀察結果、Notion page id persistence，以及單筆失敗後繼續處理。
- **純邏輯**：URL、filename、output path、weighted selection 等應以 deterministic inputs 測試。加權選擇注入固定 RNG，涵蓋 unavailable provider、excluded retry candidate、invalid pool 與無 eligible candidate；另以完整 tuple equality 鎖定預設候選設定，避免流量配置在重構時靜默漂移。實際模型與權重只在[LLM Providers、選擇與 Failover](../integrations/llm-providers.md)維護。
- **外部整合**：Notion、Discord、RSS HTTP 與 LLM provider 不應在 unit suite 發真實 request；用 response fixtures 或 mock client 固定 success/failure contract。

`ProcessingWorker` constructor factories 是新增 pipeline component 的首選 seam。新增步驟時至少測試完整成功、該步驟失敗後 task 轉 `Failed`、後續 task 不受影響，以及 lock 最終釋放。

LLM service 測試不應依賴預設池碰巧只含單一模型。需要驗證特定 failover 或「沒有替代候選」時，直接注入最小 `ModelCandidate` 清單；需要驗證預設分流時則注入固定 RNG，並同時 assert 選到的 `provider:model` 與實際 provider 呼叫。權重測試驗證的是每次請求的隨機選擇 contract，不代表嚴格的 RPM limiter。

## Nuxt 風險層

Vitest 啟用 Vue plugin、jsdom 與 globals。測試分為：

- **純 utilities**：datetime、Notion transform、staleness、dedupe/read key 與 SWR cache；注入時間或 deferred promises 驗證 concurrency。
- **Nitro handlers**：stub `useRuntimeConfig`、event 與 fetch，驗證缺設定、cache headers、forced refresh、Notion fallback、diagnostics/health 不洩密。
- **components/pages**：以 Vue Test Utils stub Nuxt globals、child components 與 localStorage，驗證搜尋、未讀排序、批次已讀、loading/error/empty 狀態及 detail Markdown。
- **SSR boundary**：用 `vue/server-renderer` 確認 server render 不碰 browser-only API，並測 hydration/default data 行為。
- **build guard**：scripts 與 config tests 保護 Nuxt internal paths shim、route rules、version footer 與 head metadata。

SWR 的核心 regression 必須同時涵蓋 fresh hit、stale immediate response/background refresh、forced refresh、沒有 snapshot 的 initial failure，以及較慢舊 refresh 不得覆蓋較新 forced result。

## Browser Extension 驗證缺口

`src/apps/extension` 目前沒有專用 automated test files。這是現況而非既有測試能力：service worker 的 URL routing/status handling、content script 的 DOM selectors、options validation 與 manifest permissions 主要依靠 code review 及 Chrome/Edge 手動驗證。

若後續補測試，優先把純 URL/channel 解析抽出可注入函式，並以 mock Chrome APIs 與 fetch 涵蓋影片 task、RSS subscription、duplicate、timeout 及 content-script fallback；manifest permission 與實際 YouTube DOM 仍需保留小型 browser smoke test。

## 新增測試的放置原則

Python 測試放 `tests/test_*.py`；共用大型 inputs 放 `tests/fixtures/`。Nuxt 測試放 `frontend/nuxt-showcase/tests/*.test.ts`，Notion payload 重用 `test-data/`。優先從最小純函式或 service behavior 測起；只有跨 SSR、routing 或 DOM interaction 的風險才升級為 mounted page test。

## 延伸閱讀

- [模組邊界與外部依賴](../architecture/module-boundaries-and-dependencies.md)
- [HTTP API 與 Client 契約](../interfaces/http-api-and-clients.md)
- [任務、鎖與結果持久化](../persistence/task-and-result-storage.md)
- [LLM Providers、選擇與 Failover](../integrations/llm-providers.md)
- [任務生命週期與併發控制](../workflows/task-lifecycle.md)
- [媒體轉錄與摘要流程](../workflows/media-processing.md)
- [Nuxt Showcase 使用體驗與資料快取](../frontend/showcase-experience.md)
