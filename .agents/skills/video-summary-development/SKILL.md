---
name: video-summary-development
description: 在本 repository 執行 Video Summary 功能開發與修正的協作流程，涵蓋需求規劃、獨立 WorkTree、feature 分支、實作驗證、review 與本機提交。適用於推進開發任務；純程式碼問答不需啟動完整流程。
---

# Video Summary 開發流程

使用繁體中文溝通；產品名稱使用 **Video Summary**，repository 名稱可能仍是 `openai-whisper`。
先讀 repository 根目錄與修改範圍內的 `AGENTS.md`，開發命令參考 `CONTRIBUTING.md`、`Makefile` 與 CI。
這份 skill 補充協作流程，不取代 repository 規則，也不代表使用者授權所有後續階段。

## 1. 了解需求與現況

- 區分本次是分析、擬定計劃、實作、commit，或發布；執行已授權的階段即可。
- 先看相關原始碼、測試與設定。使用者問「以前是不是刻意這樣做」時，查 `git log`、`git show`，區分歷史證據與推測。
- 說明目前行為、預期行為、資料與相容性影響；提供實際參考檔案。依 `AGENTS.md` 的條件才查 OpenWiki，不在任務開始時預載。
- 需求已明確時直接推進，不反覆詢問是否開始；遇到真正影響範圍的歧義才詢問。

## 2. 開發規劃

計劃應包含修改範圍、成功與失敗行為、主要步驟、驗收方式、已知限制與本次不處理的事項。
不要把一次性的功能設計（例如某種媒體鎖）升格為所有開發都必須採用的架構。

## 3. 在獨立 WorkTree 開發

- 開始修改前確認 `git status`、目前分支、base commit 與既有 WorkTree；保留使用者未提交的修改。
- 正式功能開發優先使用獨立 WorkTree，分支使用 `feature/<簡短功能名稱>`；先確認名稱未被占用。
- 延續已存在的功能 WorkTree 時重用它，不重新建立一份。新任務的 base 依使用者指定或 repository 的 master／預設 base，不能無意間疊在無關功能分支上。
- Orca 管理的 WorkTree 使用可用的 Orca skill 與該版本 CLI 指南，不猜指令。若 CLI 自動產生其他分支前綴，在修改或提交前切換到正確的 `feature/*` 分支，並核對實際分支。
- 未使用 Orca 管理狀態時可使用 Git WorkTree。遇到 sandbox 權限限制，依工具流程處理，不以改寫主目錄或繞過權限替代。
- 建立後回報 WorkTree 路徑與分支；不要提交 `.env`、下載產物、credential 或複製 secrets 到新工作區。

WorkTree 不等於交棒：可以在新目錄自行完成。只有使用者或適用 skill 明確授權委派時才啟動另一個 agent。
若採完整交棒，提供需求、驗收、參考位置與禁止發布的邊界，確認接收並回報 agent handle；不得把「已接收」說成「已完成」。
若要求監督到完成，遵循對應 orchestration 流程，不能只派出後停止追蹤。

## 4. 實作、驗證與 review

- 行為改動先建立會失敗的測試／可執行檢查，再做最小實作；純文件或 scaffolding 不需為文字內容增加測試。
- 優先沿用既有分層與抽象。Pipeline 操作集中共用，修改時確認 legacy／LangGraph 的可觀察行為一致。
- 涉及檔案刪除、lease 或多 worker 時，驗證失敗保留、使用中資料保護與並行影響；明確揭露序列化等吞吐量取捨。
- 從 repository root 使用專案鎖定環境：`uv sync --project apps/whisper_summary --frozen --no-install-project`。Python 版本依當前 pyproject 與 CI，不寫死這次使用的版本。
- 先跑修改範圍的 unittest，再跑 `make lint` 與 `git diff --check`；依風險擴大到 integration、完整測試或其他 app 檢查。命令與位置以當前 Makefile／CI 為準。
- Mock 外部服務的測試不代表已驗證真實 yt-dlp、LLM、Notion 或部署。保留完整失敗輸出，修正後重跑受影響檢查。
- review 實際差異與新檔案，確認需求、錯誤處理、設定預設值、相容性與文件一致；有新修改就重跑相關檢查。
- 使用者操作或設定改變時同步更新 `readme.md`、`.env.example` 等文件；不手改 generated OpenWiki。

## 5. 進度回報與完成交付

- 更新以「已完成、目前問題、下一步」為主，區分開始、實作完成與驗證完成，不猜百分比。
- 使用者要求每分鐘回報時，在工作進行期間約每 60 秒查證並回報，避免長時間阻塞；完成就給最終結果並停止重複回報。不要宣稱已設定背景通知，除非真的建立且獲授權。
- 子 agent 的完成訊息是線索；回報前核對實際 diff、測試結果與 Git 狀態。
- 完成摘要交代行為改變、驗證及未驗證項目、重要限制、WorkTree／分支，以及 commit／push／合併是否已執行。

## 6. 本機 commit 與遠端發布

使用者授權本機 commit 後：確認正確的 `feature/*` 分支，只 stage 本次檔案，檢查 staged diff 與 secrets hook，建立聚焦的 commit。
不要以 `--no-verify` 跳過失敗 hook；修正原因並重試。回報 commit hash、subject 與剩餘未提交修改。
不因前一個任務曾授權 commit，就自動提交後續獨立任務。

**本機 commit 不代表 push 授權。** 任何 push、遠端歷史改寫、PR 發布／合併或部署，均遵循根目錄 `AGENTS.md` 的當次確認規則。
push 前依實際 remote／branch 與全部未推送 commits，用繁體中文提供完整異動、使用影響、驗證與 workflow／部署預期，再停下取得當次確認。
範圍改變要重新取得確認；使用者只索取指令時不得代執行。
