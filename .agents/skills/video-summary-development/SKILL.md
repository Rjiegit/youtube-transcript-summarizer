---
name: video-summary-development
description: 在本 repository 執行 Video Summary 功能開發與修正的協作流程，涵蓋需求規劃、獨立 WorkTree、feature 分支、實作驗證、review、本機提交與 WorkTree 安全收尾。適用於推進開發任務；純程式碼問答不需啟動完整流程。
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
- 正式功能開發優先使用獨立 WorkTree，功能分支依下方命名規範建立；先確認名稱未被占用。
- 延續已存在的功能 WorkTree 時重用它，不重新建立一份。新任務的 base 依使用者指定或 repository 的 master／預設 base，不能無意間疊在無關功能分支上。
- Orca 管理的 WorkTree 使用可用的 Orca skill 與該版本 CLI 指南，不猜指令。若 CLI 自動產生其他分支前綴或省略日期，在修改或提交前調整為符合命名規範的分支，並核對實際分支。
- 未使用 Orca 管理狀態時可使用 Git WorkTree。遇到 sandbox 權限限制，依工具流程處理，不以改寫主目錄或繞過權限替代。
- 建立後回報 WorkTree 路徑與分支；不要提交 `.env`、下載產物、credential 或複製 secrets 到新工作區。

### 功能分支命名

格式：`feature/YYYYMMDD-<功能名稱>`，例如 `feature/20261017-media-cleanup-on-success`。

- 日期採建立功能分支當日的 `Asia/Taipei` 日期，年份四碼、月日兩碼，連續八碼、不加分隔符號。延續開發、rebase 或追加 commit 時保留原日期，不隨執行日改名。
- 功能名稱使用簡短英文小寫 kebab-case，以 `-` 連接單字，描述具體功能或目的；避免空白、底線及只有 `update`、`changes` 等模糊名稱。
- 建立前檢查本機及已知遠端 refs 是否同名；同名且屬於同一任務時優先重用，不能直接覆寫。若是不同任務，使用更明確的功能名稱區分。
- WorkTree 目錄名稱可使用相同功能名稱；以實際 Git branch 為準，不要求目錄與分支完全同名。
- 修正本機分支名稱使用 `git branch -m`，保留 commits；先確認該分支是否由其他 WorkTree 使用。已推送的分支若需改名，另依遠端 Git 寫入規則處理，不自動推送或刪除遠端分支。
- 此規範適用於功能分支；不因此改名 `master`／`main`，也不批次修改其他既有分支。

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
- review 與驗證完成後，主動引導使用者確認收尾選項：是否將功能 squash 合併到主分支，以及合併驗證後是否刪除本機功能分支／WorkTree。提供具體分支、異動摘要與保存狀況再請使用者決定；若已明確授權相同步驟，不重複詢問。不要把尚待確認的步驟說成已完成。

## 6. 本機 commit 與遠端發布

使用者授權本機 commit 後：確認正確的 `feature/YYYYMMDD-<功能名稱>` 分支（使用者明確指定其他分支時依其指示），只 stage 本次檔案，檢查 staged diff 與 secrets hook，建立聚焦的 commit。
不要以 `--no-verify` 跳過失敗 hook；修正原因並重試。回報 commit hash、subject 與剩餘未提交修改。
不因前一個任務曾授權 commit，就自動提交後續獨立任務。

**本機 commit 不代表 push 授權。** 任何 push、遠端歷史改寫、PR 發布／合併或部署，均遵循根目錄 `AGENTS.md` 的當次確認規則。
push 前依實際 remote／branch 與全部未推送 commits，用繁體中文提供完整異動、使用影響、驗證與 workflow／部署預期，再停下取得當次確認。
範圍改變要重新取得確認；使用者只索取指令時不得代執行。

## 7. Squash 合併與功能分支收尾

本專案功能完成後優先採 squash 合併，讓主分支以一筆聚焦 commit 保存該功能。
只有使用者明確授權本機合併後才執行；提供待合併分支、目標主分支（以實際 `master`／`main` 為準）、功能摘要與驗證結果。
本機 squash 合併、刪本機分支、刪 WorkTree 與遠端操作是不同範圍，不能互相推定授權。

### 本機 squash 合併

1. 確認目標工作目錄乾淨、功能分支包含預期 commits，並比較完整差異。需要 rebase 時依任務授權與實際差異處理；不能意外納入其他功能。
2. 在目標主分支執行 `git merge --squash <功能分支>`，檢查 staged diff；若有衝突，依需求與測試解決，不直接採用整份 ours／theirs 掩蓋差異。
3. 對合併後內容重跑相關測試、lint 與差異檢查，建立一筆描述最終功能的 commit。失敗時先修正，不將未通過的結果宣稱為可交付。
4. 回報主分支上的 squash commit、功能異動與驗證結果。不要因本機合併而自動 push 或發布／合併遠端 PR；遠端仍依 `AGENTS.md` 當次確認規則。

### 刪除本機功能分支

- squash 合併驗證通過後，提醒使用者功能已保存在主分支，並提供可刪除的本機分支名稱；取得刪除授權後執行，已授權合併後刪除者可直接繼續。
- 刪除前確認分支沒有合併後追加的獨有修改；以 merge-base、squash commit 與實際檔案／patch 差異核對功能完整保留，不能只依 commit 標題或祖先關係判定。
- squash 不保留原 commit 祖先關係，`git branch -d` 可能拒絕。只有確認完整內容已保存且已授權刪除，才可使用 `git branch -D <功能分支>`；內容不一致先保留分支並釐清。
- 先用 `git worktree list` 確認分支是否仍被 WorkTree 使用；若仍使用，先依下一節完成環境保存檢查與授權移除，不能為刪分支跳過資料保存。
- 刪分支會失去原功能 commits 的一般分支入口；若使用者需要保留逐筆開發歷史，先以已授權的 ref 保存再刪除。主分支的 squash commit 保存最終功能，不代表保留原 commit 歷史。
- 刪除後確認本機分支已消失、主分支 squash commit 仍存在，回報結果；不連帶刪除遠端分支或其他既有本機分支。

## 8. WorkTree 收尾與刪除

開發完成不代表自動授權刪除環境；使用者要求清理 WorkTree，或已明確授權完成後清理時才執行。
已授權且保存檢查通過即可繼續，不必再次詢問相同的刪除許可。

刪除前逐項核對：

- **對象與程序**：以 `git worktree list` 與管理工具確認完整路徑、分支、HEAD；確認沒有仍在執行的開發、測試或寫檔工作。只處理指定 WorkTree，不影響主工作目錄及其他 WorkTree。
- **程式修改**：檢查 staged、unstaged 與 untracked 檔案。需要保留的修改必須已 commit，或已另存到 WorkTree 外並驗證；未取得 commit 授權時，不能自行提交來通過檢查。
- **Commit 保存**：記錄 HEAD 及功能 commits，確認有刪除後仍會存在的本機分支或 tag 可到達它們。Detached HEAD 或只有 reflog 可找回不算保存完成。尚未合併、未 push 不妨礙移除 WorkTree，但必須保留對應 ref 並提醒使用者。
- **本機資料**：乾淨的 `git status` 不代表資料已保存。另檢查 ignored 檔案（例如 `git status --short --ignored`）、`.env`、SQLite、`data/`、手動筆記、測試報告與產物；區分可重建依賴／cache 與唯一資料。僅列必要路徑，不輸出 secrets 或資料內容。
- **備份確認**：唯一資料須保存在 WorkTree 外，核對備份存在、大小或 checksum 等適當證據。遇到符號連結或共享目錄，要確認實際資料位置與移除工具行為，不能假設已備份，也不能連帶刪除共享資料。

刪除前簡短提醒使用者：將移除的環境路徑、已保存的 commit／分支、資料保存位置或可重建項目，以及是否尚未合併／push。
若仍有未保存修改、唯一資料、無法確認的刪除副作用或運行中的寫入程序，先保留環境並說明缺口；只詢問必要的保存或捨棄決策，不用 `--force` 略過問題。

Orca 管理的 WorkTree 使用對應 CLI；先確認刪除是否也會嘗試刪分支、停止 terminal 或執行 hooks。
若工具可能刪除唯一保留 commits 的 ref，先在授權範圍內建立並驗證保留 ref，或使用能保留分支的移除方式。
不要為了刪除 WorkTree 自動 push、合併、部署或執行未授權的遠端操作。

刪除後重新核對 WorkTree 清單、環境路徑與保留分支的 HEAD，確認 commits 仍可讀取。
回報移除結果、保留的分支與 commit、資料保存情況及後續尚待合併／push 的事項；工具回傳「正在移除」時不能直接當作已完成。
