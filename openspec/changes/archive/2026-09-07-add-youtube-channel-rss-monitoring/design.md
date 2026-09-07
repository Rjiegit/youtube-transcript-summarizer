## Context

目前系統已具備手動或 API 建立任務後自動啟動 processing worker 的能力，但缺少「來源自動發現」機制。對於固定追蹤的 YouTube channel，使用者仍需手動貼 URL，造成漏件風險與額外維運負擔。

本次變更需要跨越設定層、背景排程、任務建立流程與觀測資訊輸出，且需與既有 processing lock 相容，避免引入重複 worker 或重複任務。
另外，為了讓追蹤名單可由使用者維護，需要在 Streamlit 提供可操作介面，並以 SQLite 持久化訂閱清單。

## Goals / Non-Goals

**Goals:**
- 提供可設定的 YouTube channel RSS 輪詢機制，定期抓取最新影片。
- 提供 Streamlit 介面管理追蹤 channel（新增、編輯、啟用/停用、刪除）。
- 對新影片做去重，僅在首次觀測到時建立任務。
- 與既有任務建立及自動處理流程整合，維持 processing lock 行為一致。
- 提供最小可用觀測資訊（最近輪詢時間、成功/失敗、錯誤原因）。

**Non-Goals:**
- 不提供多使用者權限/角色管理。
- 不提供複雜排程 UI（僅提供輪詢間隔與 channel 清單管理）。
- 不處理非 YouTube RSS 來源。

## Decisions

1. Decision: 使用獨立 RSS monitor service，定期輪詢 feed 並呼叫既有 task 建立介面。
   - Rationale: 降低對現有 pipeline 的侵入，保留現有 API/task workflow 的單一真相來源。
   - Alternatives considered:
     - 直接在 `processing_runner` 內嵌 RSS 抓取：耦合過高，測試與維護困難。
      - 以外部 cron + CLI 驅動：部署分散，跨環境一致性較差。

2. Decision: 追蹤 channel 清單使用 SQLite 資料表持久化，並由 Streamlit 介面管理。
   - Rationale: 使用者可在不改 `.env` 情況下動態維護追蹤來源，且服務重啟不遺失設定。
   - Alternatives considered:
     - 以環境變數維護清單：操作不便且需重啟才能更新。
     - 以檔案（JSON/YAML）維護：可行但缺少結構化查詢與併發更新保護。

3. Decision: 預設輪詢間隔為每 1 小時（3600 秒），並允許透過設定覆寫。
   - Rationale: 每小時輪詢可平衡更新即時性與外部請求成本，同時保留不同部署場景的調整彈性。
   - Alternatives considered:
     - 預設 5-15 分鐘：即時性較高但請求成本較高。
     - 固定不可調整：簡單但缺乏環境彈性。

4. Decision: 去重鍵採用 `video_id`（由 YouTube URL 解析）優先，退回 canonical URL。
   - Rationale: `video_id` 穩定且可跨參數變化去重。
   - Alternatives considered:
     - 僅以 title+published 比對：易受標題調整影響。
     - 完整 URL 字串比對：`utm` 或 query 參數可能造成重複。

5. Decision: 使用 `published` watermark 作為第一層過濾，再以 `video_id` 做最終 idempotent 去重。
   - Rationale: 先用時間水位降低每輪比對成本，再用唯一識別避免同秒或重排造成漏抓/重抓。
   - Alternatives considered:
     - 僅用時間水位：可能在邊界時間發生重複或漏抓。
     - 僅用 `video_id` 全量比對：正確但輪詢成本較高。

6. Decision: 監控狀態與每 channel watermark 寫入 SQLite，避免重啟後重複掃描。
   - Rationale: 既已引入 channel 訂閱表，順勢持久化監控狀態可提升一致性與可觀測性。
   - Alternatives considered:
     - 僅記憶體快取：實作簡單但重啟後易重複建立任務。

7. Decision: 失敗策略採「本輪記錄錯誤、下輪再試」，不阻塞其他 channel。
   - Rationale: 提升整體可用性，避免單一 feed 問題造成全域停擺。
   - Alternatives considered:
     - 任何 feed 錯誤即中止整輪：故障範圍過大。

8. Decision: 套件選型採 `feedparser` + `python-dateutil`，HTTP 請求沿用既有 client。
   - Rationale: 以成熟解析器處理 Atom/RSS 細節與時間格式，降低自製 parser 風險。
   - Alternatives considered:
     - 純手寫 XML 解析：維護成本高且容錯較差。
     - 改用大型排程/爬蟲框架：超出本次需求。

## Risks / Trade-offs

- [RSS feed 延遲或格式異常] → Mitigation: 解析失敗時保留原始錯誤與 feed URL，下一輪自動重試。
- [去重狀態非強一致，重啟後可能短暫重複建立] → Mitigation: 任務建立前再做一次既有任務查重（同 URL/video_id）。
- [輪詢過頻造成 API/網路壓力] → Mitigation: 以環境變數限制最小間隔，預設保守值。
- [僅靠 `updated` 欄位造成誤判新影片] → Mitigation: 以 `published` 為水位基準，`updated` 僅作輔助觀測。
- [UI 與 monitor 並行更新訂閱資料造成讀寫衝突] → Mitigation: 以單筆 transaction 與樂觀更新（updated_at）處理。

## Migration Plan

1. 新增 SQLite schema migration：建立 channel 訂閱表與必要索引。
2. 在 Streamlit 上線 channel 管理介面（先隱藏於 feature flag 可選）。
3. 啟用 monitor 並在 dev/staging 驗證 UI 建立的 channel 可被輪詢與正確去重。
4. 觀察錯誤率與重複率後再擴大 channel 清單。
5. 若需回滾，關閉 RSS monitor 與 UI 入口；既有手動/API 建立任務流程維持不變。

## Open Questions

- 是否需要在 UI 顯示每個 channel 最近成功輪詢時間與錯誤摘要？
