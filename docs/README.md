# 操作文件導覽

README 保留專案簡介、最短啟動與功能入口；本目錄人工維護完整操作步驟、必要設定及內容規則。OpenWiki 由程式與測試產生實作說明，負責模組關係、資料流、內部機制與證據。

## 依功能找文件

| 目的 | 操作手冊 | OpenWiki 實作導覽 |
| --- | --- | --- |
| 切換 engine、啟動與管理 Worker | [Processing](operations/processing.md) | [任務生命週期](../openwiki/workflows/task-lifecycle.md)、[媒體處理](../openwiki/workflows/media-processing.md) |
| 保留／清理媒體 | [媒體清理](operations/media-cleanup.md) | [媒體處理](../openwiki/workflows/media-processing.md) |
| 設定 Discord 摘要入口 | [通知](operations/notifications.md) | [完成通知](../openwiki/workflows/media-processing.md#完成通知與知識庫導向) |
| 設定 Showcase、分享網址與部署核對 | [Showcase](operations/showcase.md) | [使用體驗與快取](../openwiki/frontend/showcase-experience.md) |
| 安裝已讀同步、輪替與重新連結 | [已讀同步](operations/showcase-read-sync.md) | [Session 與資料合併](../openwiki/frontend/read-state-sync.md) |
| 安裝及管理影片收件匣 | [影片收件匣](video-inbox.md) | 尚無獨立頁面；入庫後見 [任務生命週期](../openwiki/workflows/task-lifecycle.md) |
| 整理週報、維護分析規則與資料契約 | [每週回顧](features/showcase-weekly-insights.md) | [週報建置流程](../openwiki/workflows/weekly-insights.md) |

## 維護規則

- 完整安裝、操作、輪替與復原步驟只維護於 docs；README 保留摘要與連結。
- 實作結構、API 機制、演算法與測試證據由 OpenWiki 說明；docs 只保留操作必要的行為限制。
- 功能新增或變更時更新本導覽與 README 入口；保留既有文件路徑，避免讓 skill 或 Wiki 連結失效。
- OpenWiki 更新時引用對應操作手冊，不複製完整操作步驟；本目錄是產生 Wiki 時的文件責任依據。
- OpenWiki 頁面與 provenance 透過正式 lifecycle 更新，不手改 generated metadata。更新後檢查本表、反向連結與已過時敘述。
- 過往資料數字應標示觀察日期；單次測試數量、未推送或未部署狀態不作為長期操作說明。
- 文件與執行結果有差異時，以原始碼與測試為準，核對後更新文件，不以複製內容維持兩份相同說明。
