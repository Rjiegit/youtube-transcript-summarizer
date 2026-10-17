# 媒體保留與清理操作


`DELETE_MEDIA_ON_SUCCESS=true`（預設）會在本機摘要保存、Notion 發布與任務
`Completed` 寫入成功後，刪除下載器回傳的單一媒體檔。狀態更新明確回傳失敗時保留媒體並中止流程。可設為 `false` 保留媒體排錯。
legacy 與 LangGraph 行為一致；Discord 通知失敗及清理失敗只記錄警告，不會將成功任務改為 Failed。
檔案已不存在視為清理完成。只清理 `data/videos` 內的媒體，拒絕路徑越界、父目錄穿越、
符號連結與非一般檔案；不掃描資料夾、不按影片 ID wildcard 刪除，也不刪摘要、
metadata、SQLite 或模型快取。

## 共用資料與手動清理

所有 worker 必須共用相同資料目錄，檔案系統須支援 POSIX `flock`。請勿刪除 `data/` 下的媒體使用鎖檔。
獨立下載指令、外部程式與手動清理不受 processing engine 的鎖協調，請在 worker 停止後操作。
失敗、lease 遺失及中斷的媒體保留供重試。需保留成功媒體排錯時，設定 `DELETE_MEDIA_ON_SUCCESS=false` 並重啟 worker。

手動清理前先在 repository 根目錄預覽：

```bash
make cleanup-data-dry-run
```

確認目標後再執行 `make cleanup-data`；其預設 3 天保留政策會影響影片與摘要，與成功任務只清理單一媒體檔的範圍不同。

## 實作導覽

鎖的粒度、路徑保護與失敗處理見 [媒體處理](../../openwiki/workflows/media-processing.md)；一般資料清理設定見 [設定與部署](../../openwiki/operations/configuration-and-deployment.md#本機-data-清理)。
