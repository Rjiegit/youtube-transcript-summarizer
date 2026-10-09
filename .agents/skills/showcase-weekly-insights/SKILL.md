---
name: showcase-weekly-insights
description: 從 Notion 文章摘要整理 Showcase 週報與分類趨勢，依本機逐週進度補跑未完成週、更新進行中週或指定範圍重算。適用於手動定期整理每週回顧。
---

# Showcase 週報整理

在 openai-whisper repository 內操作。產出繁體中文週報文件與整體分類趨勢，沿用 `apps/showcase/content/weekly-insights/` 契約，不新增網站實作或自動排程。

先讀 repository 的 `docs/features/showcase-weekly-insights.md`，確認分類、來源去重與展示文件欄位。進度工具位於本 skill 的 `scripts/progress.py`，以下命令從 repository 根目錄執行；若 skill 安裝於其他位置，用實際路徑呼叫。

## 決定此次範圍

```bash
python3 .agents/skills/showcase-weekly-insights/scripts/progress.py plan
```

- 週日到週六、Asia/Taipei；起點讀 `series.json.collectionStart`，目前為 2026-09-01。首週 8/30 開始但只收 9/1 起資料。
- 預設到最近已結束的週六，按時間順序處理 `weeks`，跳過有有效完成紀錄的週。沒有待辦就回報目前已完成範圍，不重新呼叫 Notion／LLM。
- 使用者指定截止日期時加 `--through YYYY-MM-DD`。日期選取包含該日的整週，已結束週保留完整七天，不切成日報。包含本週須加 `--include-open`；本週資料只讀至選定日期／查詢當下。
- 使用者要重新分析既有週或追查 Notion 後續修改時，加 `--from YYYY-MM-DD --through YYYY-MM-DD --refresh`。不要把歷史首次收錄時間改成最後編輯時間。
- 進度逐週記錄於 `data/reports/weekly-insights/progress.json`，包含完成狀態、版本指紋、報告指紋與私人快照。中途缺週、已記錄但尚未結束的週、報告變動或來源快照遺失都會列入待辦。不要只看最新日期跳過較早缺口。
- 若進度不存在，先檢查已有週報與其私人快照；確認來源、分類、完整性後用 `bootstrap --snapshot <私人快照路徑>` 登記既有結果。無可核對的快照則從起點補跑，不能把檔案存在當作成功。

## 讀取與整理

使用可用的 Notion connector 或 repository 現有 adapter。權限只涵蓋讀取文章與更新本機文件，不修改 Notion。憑證由 `.env`／既有設定載入，不列印或寫入輸出文件。連線或分頁失敗時保留已完成進度並回報受阻週，不能用不完整資料補成零。

1. 每次執行保存不可變的私人快照於 `data/reports/weekly-insights/runs/{執行時間}/`，包含查詢範圍、asOf、分頁是否完成、頁面 ID、created_time、last_edited_time、來源鍵與摘要正文。需要正文時完整讀取 block 分頁；查詢必須完整分頁，不能只取第一頁或最後一個月。
2. 以 Notion created_time 轉台灣日期，使用 `[週日, 下週日)` 分週。沿用文件定義的 YouTube video ID／URL／page ID 來源鍵。同週去重、跨週保留；新來源判斷使用從 collectionStart 起的來源索引，不能只看這次補跑範圍。載入先前私人快照補足索引，缺漏時先補取歷史來源，不需重寫已核對的週報正文。
3. 固定八個主分類與 analysisVersion，同一來源的分類保持一致。只有需要改變分析規則時才改版本；版本變動會讓 planner 要求重算。空週只有在確定完整取得資料後才可寫零。
4. 產出每週主題、代表來源、分類數量與占比；使用完整週比較百分點，不將首週部分資料或本週進行中資料與完整週量直接比較。摘要品質不足時保留品質說明，不根據標題猜測文章內容。文章內的外部主張不是已驗證事實。
5. 更新週日目錄 `report.json`、`report.md`、series 的 manifest／全期去重數及 overview。新增週先作 draft，核對展示內容後才設 `published: true`，此旗標只代表進入本機網站 bundle。實質修改既有週增加 revision，覆用原 slug，不另建重複週。

目前驗證器要求所有週報與 series 共用 asOf。同步未重算的已結束週 asOf 時，不聲稱重新查詢過它們，也不因此增加 revision；進度指紋排除 asOf／publishedAt，原始查詢時間仍保留在各週進度紀錄。進行中週變 closed 前必須重新完整讀取該週，不能只改旗標。

## 核對與保存進度

```bash
npm --prefix apps/showcase run insights:check
python3 .agents/skills/showcase-weekly-insights/scripts/progress.py record \
  --week YYYY-MM-DD --snapshot data/reports/weekly-insights/runs/RUN/snapshot.private.json
```

`record` 會再次執行內容驗證，要求該週已完成本機展示核對、資料完整且有私人快照；成功後才原子寫入進度。open 週可記錄本次成果，但下次仍重跑。一週成功立即 checkpoint，避免多週補跑中斷後全部重做；失敗週不登記成功，不手改進度跳過它。

每次只執行一個整理流程。進度寫入有 `.lock` 防止並行寫入；若中斷留下 lock，先確認沒有另一個正在寫入的流程，再移除 lock 並續跑 plan。保留私人快照，不覆寫已被進度引用的檔案。

完成後再跑 plan 確認剩餘缺口，檢查 diff 與週報頁面。沿用開發文件的測試／build／SSR 流程；重新啟動 dev 才載入新內容。若同一個 dev 程序正在使用 Nuxt 產物，先停止該程序再 build，完成後恢復開發頁。

向使用者回報本次處理、跳過、失敗與待補的週、資料截至時間及進度檔位置。更新文件與進度不代表遠端發佈：commit/push、發布或部署依 repository AGENTS.md 當次確認規則辦理；使用者要手動推送時只留下本機可檢查結果。
