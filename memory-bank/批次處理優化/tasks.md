# 批次處理優化 - 任務列表 (Dynamic Queue / 無資料庫)

## 🎯 目標摘要
實作「單輸入框 + 動態隊列 + 自動順序處理」的 Streamlit 功能：
1. 使用者可隨時輸入 YouTube URL 並加入隊列
2. 任務按加入順序自動處理（下載→轉錄→摘要→結果存檔）
3. 失敗任務記錄並繼續下一個
4. 全程無資料庫、僅使用 Session State
5. 不破壞現有單檔處理功能

## 🧩 Session State 結構 (參考)
```python
dynamic_queue = {
    "current_url_input": "",
    "task_queue": [],
    "current_index": 0,
    "is_processing": False,
    "should_stop": False,
    "results": [],
    "error_log": [],
    "stats": {"total": 0, "waiting": 0, "processing": 0, "completed": 0, "failed": 0}
}
```

## 🚀 Phase 1 (核心功能 / 1週)

### T1: 狀態初始化與工具函數
目標: 建立 `init_dynamic_queue_state()` 與統計更新 `update_stats()`
驗收:
- [ ] 初次載入自動建立結構
- [ ] 重置功能可清空所有狀態
- [ ] 統計欄位正確計算
檔案: `streamlit_app.py` / `queue_state.py`

### T2: URL 驗證與加入隊列
目標: 實現 `add_url(url)` 與 YouTube URL 驗證
驗收:
- [ ] 非法 / 重複 URL 阻擋並提示
- [ ] 合法 URL 添加後輸入框清空
- [ ] 任務初始狀態 `waiting`
檔案: `url_validator.py` / `dynamic_queue_manager.py`

### T3: 動態處理循環 (processing_loop)
目標: 單步處理 + `st.rerun()` 推進
驗收:
- [ ] 可從第一個 waiting 任務開始
- [ ] 任務完成 / 失敗後自動前進
- [ ] 無任務或結束時自動停機
檔案: `dynamic_queue_manager.py`

### T4: UI - 隊列與控制面板
目標: 繪製輸入/隊列/控制/進度區域
驗收:
- [ ] 單輸入框 + 添加按鈕
- [ ] 列出全部任務 + 狀態徽章
- [ ] 顯示總進度 (完成 / 總數)
- [ ] 提供「開始 / 停止 / 清空」
檔案: `streamlit_app.py`

### T5: 任務處理整合現有流程
目標: 重用現有下載、轉錄、摘要邏輯
驗收:
- [ ] 成功結果寫入 `results`
- [ ] 失敗寫入 `error_log`
- [ ] 不修改既有單檔處理代碼介面
檔案: `dynamic_queue_manager.py` / 使用既有模組

### T6: 錯誤紀錄與重試
目標: 顯示錯誤表格 + 單筆重試
驗收:
- [ ] 顯示錯誤時間/URL/訊息
- [ ] 重試重新排入末尾 (或改回 waiting)
- [ ] 重試計數遞增
檔案: `streamlit_app.py`

## 🔧 Phase 2 (優化 / 1週)

### T7: 使用者體驗優化
內容: Expander 包裝長摘要 / 高亮當前任務 / 進度條細節
驗收:
- [ ] 當前任務高亮
- [ ] 長結果折疊顯示
- [ ] 處理中顯示 Spinner

### T8: 效能與狀態最小化
內容: 只保存必要欄位、摘要截斷、結果延遲渲染
驗收:
- [ ] 大量任務 (>50) 仍流暢
- [ ] 無冗餘大型字串駐留

### T9: 單元測試
範圍:
- [ ] URL 驗證
- [ ] add_url 去重與格式
- [ ] 任務狀態轉換
- [ ] processing_loop 成功/失敗分支
檔案: `tests/test_dynamic_queue.py`

### T10: 集成測試
場景:
- [ ] 連續添加 + 依序處理
- [ ] 失敗後不中斷
- [ ] 重試後成功
- [ ] 混合新增與處理

### T11: 文檔與 README 更新
內容:
- [ ] README 新增「動態隊列模式」章節
- [ ] 使用指南 + 常見問題
- [ ] 加入限制說明 (無持久化、刷新即清空)

## 📊 時程 & 里程碑
Milestone 1 (週末): T1~T6 可用最小版本
Milestone 2 (週末): T7~T11 完成，準備合併

## ✅ 驗收總表
| 編號 | 項目 | 狀態 | 備註 |
|------|------|------|------|
| T1 | 狀態初始化 | ✅ | 建立 queue_state.py + 統計重算 |
| T2 | URL 驗證/加入 | ✅ | add_url + 去重 + 驗證 |
| T3 | 處理循環 | ✅ | processing_loop 單步推進 + 自動前進 |
| T4 | UI 隊列/控制 | ✅ | 輸入/列表/控制/進度已完成 |
| T5 | 任務與流程整合 | ✅ | 重用既有下載/轉錄/摘要模組 |
| T6 | 錯誤與重試 | ✅ | 錯誤記錄 + 重試機制 (retry_count) |
| T7 | 體驗優化 | ☐ |  |
| T8 | 效能優化 | ☐ |  |
| T9 | 單元測試 | ☐ |  |
| T10 | 集成測試 | ☐ |  |
| T11 | 文檔更新 | ☐ |  |

## 🧪 測試策略摘要
單元: 函數級 / 任務狀態 / 驗證
集成: 多任務連續、錯誤隔離、重試
邊界: 空隊列、重複 URL、停止中新增

## 🔮 後續可選擇延伸 (不在本階段)
- 持久化 (JSON / SQLite 可選開關)
- Web API / 外部觸發
- 並發處理 (限制 CPU / I/O)
- 任務優先權 / 排序策略

---
**版本**: tasks v2.0 (Aligned w/ design v1.1)  
**最後更新**: 2025-08-19