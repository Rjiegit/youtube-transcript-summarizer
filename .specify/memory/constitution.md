<!--
Sync Impact Report
- Version change: N/A → 1.0.0
- Modified principles: 初版建立
- Added sections: 核心原則、附加技術與安全約束、開發流程與品質關卡、治理
- Removed sections: 無
- Templates requiring updates: ✅ .specify/templates/plan-template.md; ✅ .specify/templates/spec-template.md; ✅ .specify/templates/tasks-template.md
- Follow-up TODOs: 無
-->
# YouTube 影片文字轉錄與摘要工具 Constitution

## Core Principles

### I. 極簡與乾淨程式碼
採用最小可行變更與 Clean Code 原則：先用最簡單解決方案交付價值，再視需求演進；避免過早抽象與過度設計；函式與模組職責單一、命名清晰、無死碼與重複碼；保持 PEP 8、型別註解與 127 字元行長限制，確保可讀性與維護性。

### II. 代碼品質與審查紀律
所有變更 MUST 通過靜態檢查（flake8）與必要的型別/安全檢查；PR 需說明目的、影響範圍與風險，並在審查中對照本憲章逐項檢查；配置與秘密值全部使用環境變數與 `.env`，嚴禁硬編碼。

### III. 測試標準與自動化
新功能、修正與重構 MUST 具備對應的單元或整合測試，涵蓋輸入驗證、錯誤處理與主要分支；外部服務（LLM、yt-dlp、Notion）需以 mock/fake 隔離，測試保持可重現且與網路解耦；`make test` 為交付前的必跑關卡。

### IV. 使用者體驗一致性
CLI、API、Streamlit 介面 MUST 提供一致且清楚的訊息、錯誤回饋與預設值；使用者流程以「可快速完成主要任務」為核心，避免多餘步驟；日誌與摘要輸出需結構化且可追蹤，以利除錯與支持。

### V. 效能與資源效率
音訊下載、轉錄與摘要流程須避免重複 I/O，能快取即快取；對長音檔與多任務場景需關注記憶體與磁碟使用量，優先採取串流/分段策略；性能調整前先建立基準量測與目標（如處理時間、成本、佔用），並在 PR 說明改善效果。

## 附加技術與安全約束

- 主要語言為 Python；遵循 PEP 8 與專案行長限制 127。
- 機密與憑證一律來自 `.env`，不得寫入版本控制；日誌不得洩漏密鑰或個資。
- 依賴新增需評估體積與安全性，優先使用現有庫；Docker/Makefile 命令需保持向後相容並記錄。

## 開發流程與品質關卡

1. 需求/問題定義 → 將預期行為與邊界寫入 spec 或 issue，並在計畫文件中完成 Constitution Check。
2. 設計與分支：以最小增量拆分任務；非必要不引入新層級或抽象。
3. 實作：保持小步提交；對外部呼叫加入錯誤處理與超時。
4. 測試：撰寫或更新測試先於實作驗證（至少覆蓋主要 happy path 與失敗情境）；`make test` 和 `flake8 .` 必須通過。
5. 審查與發布：PR 說明需列出測試結果、性能或 UX 影響；必要時提供回滾或配置開關。

## Governance

本憲章優先於其他開發慣例。修訂需記錄變更內容、理由與版本號，並在提交時更新 Last Amended。版本號採 SemVer：新增原則或重要擴充為 MINOR，移除或重定義原則為 MAJOR，文字澄清為 PATCH。每個 PR 審查需對照核心原則與流程關卡做合規檢查；重大偏離需在 PR 中說明風險與緩解措施。

**Version**: 1.0.0 | **Ratified**: 2025-11-29 | **Last Amended**: 2025-11-29
