---
type: workflow
title: 每週回顧整理與內容發布流程
description: 從 Notion 摘要的手動整理、逐週 checkpoint 到公開文件驗證與 Nuxt registry 建置，說明週報的時間口徑、發布邊界及續跑方式。
tags: [weekly-insights, content, workflow, checkpoint, nuxt]
verified:
  - by: openwiki/0.6.0
    at: 2026-10-10T15:06:52.784Z
sources:
  - id: openwiki-source-41d6fd61738e966a1f855639
    resource: repo://.agents/skills/showcase-weekly-insights/scripts/progress.py
  - id: openwiki-source-b493016d77bf2922d5f7e385
    resource: repo://.agents/skills/showcase-weekly-insights/SKILL.md
  - id: openwiki-source-bbc421d322d74564a269df19
    resource: repo://apps/showcase/package.json
  - id: openwiki-source-17de8480042164f5a9040c86
    resource: repo://apps/showcase/scripts/weekly-insights-content.mjs
  - id: openwiki-source-263e3bdd5cbd1e9c173088e9
    resource: repo://apps/showcase/server/utils/weekly-insights.ts
generated: { by: "codex", at: "2026-10-10T15:06:52.784Z" }
---

# 每週回顧整理與內容發布流程

每週回顧是整理過的內容產品，與 Showcase 即時讀取 Notion 摘要的路徑分開。作者透過專案週報 skill 讀取並核對來源，產出 repository 中的展示文件；網站只讀取建置時打包的 registry，瀏覽時不查 Notion 或呼叫 LLM。

## 責任與產物

| 位置 | 責任 |
| --- | --- |
| `.agents/skills/showcase-weekly-insights/` | 引導來源整理、分析與逐週續跑；progress CLI 不自行讀取 Notion 或生成洞見 |
| `data/reports/weekly-insights/` | 私人來源快照與 `progress.json`，不進網站 bundle |
| `apps/showcase/content/weekly-insights/` | `series.json`、`overview.md` 與每週 `report.json`／`report.md` |
| `scripts/weekly-insights-content.mjs` | 驗證契約、投影白名單欄位並產出 registry |
| `server/utils/weekly-insights.ts` | 從已打包 snapshot 提供列表與單週資料 |

詳細操作與欄位規格以[週報功能文件](../../docs/features/showcase-weekly-insights.md)為準；訪客的篩選、導航與載入體驗見[Nuxt Showcase 使用體驗與資料快取](../frontend/showcase-experience.md)。

## 整理與 checkpoint

1. 從 repository root 執行 `make showcase-insights-plan`，逐週找出缺口。預設選取最近已結束的週；本週需明確加入 `--include-open`，歷史重查使用 `--refresh` 與日期範圍。
2. 依週報 skill 完整取得來源分頁，保存不可變私人快照，再核對正文、來源鍵、分類與完整性。查詢失敗或分頁不足不能以零筆代替。
3. 編輯該週 `report.json`／`report.md`，維護 manifest、overview 與分類洞見。新增週先作 draft；既有週的實質修改增加 revision。
4. 執行 `npm --prefix apps/showcase run insights:check`，核對本機展示後逐週登記：

```bash
python3 .agents/skills/showcase-weekly-insights/scripts/progress.py record \
  --week YYYY-MM-DD \
  --snapshot data/reports/weekly-insights/runs/RUN/snapshot.private.json
```

5. 再執行 plan 確認缺口；一週成功就 checkpoint，失敗週不記錄成功。

planner 核對每週紀錄，而非只看最新完成日期。規則改變、report 或快照變動、快照遺失、manifest 移除、先前 open 週與指定 refresh 都可能重新排入待辦。進度指紋排除 `asOf`／`publishedAt`，同步共同時間不代表歷史週重新查詢。

`record` 要求該週位於 manifest、資料完整、已核對本機展示且私人快照可讀，並先執行全系列驗證。寫入以 `.lock` 排除其他進度 writer，暫存檔經 flush／fsync 後以 `os.replace` 原子替換。open 週可保存成果但仍會再次排入待辦；clone repository 不會帶回被忽略的私人進度與快照。

## 時間與分析口徑

一週採 Asia/Taipei 的週日到週六，區間為 `[start, endExclusive)`，slug 使用週日日期。來源依收錄建立時間分週，不能當成影片發布或閱讀時間。首週可能只有部分 coverage，本週保留 open 狀態。

同週來源去重、跨週保留；每來源只計一個主分類。週次來源合計包含跨週重現，不能當成全期不同來源數。比較完整週時須同時符合 closed、complete 與 `coverageStart=start`。分類洞見與話題紀錄是已核對的質性內容；週次篩選不會即時重算它們，結論也不外推成外部市場趨勢。

## 建置與發布邊界

`predev`、`pretest` 與 `prebuild` 先執行 registry 建置。loader 只讀 manifest 內文件，驗證日期、版本、計數、分類及安全 URL／Markdown；draft 不進 registry。系列有未發布週時隱藏整體 overview、全期不同來源數及系列洞見，避免帶出未發布分析。

registry 寫至 `.generated/weekly-insights.ts`，由 server 明確 import 進 Nitro bundle；列表省略正文、代表來源與品質說明，單週詳情才提供完整資料。內容變更需重新啟動 dev 或重新建置才載入。

`published: true` 只決定內容是否進入本機 bundle。遠端 push、發布與部署仍須依 AGENTS.md 在具體結果可檢查後取得當次確認。此整理流程不會自動建立 cron 或推送；部署設定見[設定、執行與部署](../operations/configuration-and-deployment.md)。

## 驗證入口

- `npm --prefix apps/showcase run insights:check`：內容契約與公開投影。
- `apps/showcase/tests/weekly-insights-content.test.ts`：draft、計數、日期、URL 與系列內容保護。
- `apps/showcase/tests/weekly-insights-pages.test.ts`：頁面與 API 行為。
- `make showcase-insights-progress-test`：週次範圍、缺口、open、刷新、指紋與保存。

涉及網站實作時再依[開發規則與測試策略](../operations/development-and-testing.md)執行相關測試、build 與 SSR 驗證。
