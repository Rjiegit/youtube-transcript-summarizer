### **系統分析與設計**

這個計畫的核心是將目前的單次處理流程，轉變為一個可持續運行的、由資料庫驅動的批次處理系統。

**1. 核心組件 (Core Components):**

*   **前端介面 (Frontend):**
    *   建立一個新的 Streamlit 檔案 `scheduler_app.py`，專門用來讓使用者提交 YouTube 網址進行排程處理。
    *   這個介面會將使用者提交的網址寫入到後端的 Notion 資料庫，並標記為「待處理」。

*   **資料庫層 (Database Layer):**
    *   **資料庫抽象層 (Abstraction Layer):** 為了未來可以擴充支援其他資料庫 (如 PostgreSQL, SQLite)，我會建立一個通用的資料庫介面 (Interface) 或抽象基礎類別 (Abstract Base Class)。這個介面會定義標準的資料庫操作，例如 `add_task`, `get_pending_tasks`, `update_task_status`。
    *   **Notion 連接器 (Notion Connector):** 實現上述的通用介面，專門用來與 Notion API 互動。這會被封裝在一個新的檔案中，例如 `notion_client.py`。

*   **排程器 (Scheduler):**
    *   建立一個新的 Python 腳本，例如 `scheduler.py`。
    *   這個腳本會以固定的時間間隔（例如每 5 分鐘）運行。
    *   它的主要工作是：
        1.  查詢 Notion 資料庫，找出所有狀態為「待處理」的項目。
        2.  遍歷這些項目，逐一觸發影片下載、轉錄和摘要的核心處理邏輯。
        3.  在處理完成或失敗時，更新 Notion 資料庫中對應項目的狀態（例如更新為「已完成」或「失敗」並記錄錯誤訊息）。

*   **容器化 (Containerization):**
    *   更新 `docker-compose.yaml`，為新的 `scheduler.py` 建立一個獨立的服務 (service)。這可以確保排程器與 Streamlit Web UI 在各自的容器中獨立運行，互不干擾。

**2. 工作流程 (Workflow):**

1.  **使用者** 在 `scheduler_app.py` 介面輸入 YouTube 網址並提交。
2.  **`scheduler_app.py`** 呼叫 **Notion Connector**，將網址和初始狀態「待處理」(Pending) 寫入 Notion 資料庫。
3.  **Scheduler** 服務在背景定期運行，它呼叫 **Notion Connector** 取得所有「待處理」的任務。
4.  對於每一個任務，**Scheduler** 依序呼叫 `youtube_downloader`, `transcriber`, `summarizer` 等現有模組進行處理。
5.  處理完成後，**Scheduler** 再次呼叫 **Notion Connector**，將 Notion 中該任務的狀態更新為「已完成」(Completed)，並將生成的摘要內容寫回對應的欄位。
6.  如果處理過程中發生錯誤，狀態會被更新為「失敗」(Failed)，並記錄錯誤原因。

**3. Notion 資料庫結構建議:**

我建議在您的 Notion Workspace 中建立一個新的 Database，並包含以下欄位 (Properties):

| 欄位名稱 (Property Name) | 類型 (Type)         | 描述 (Description)                               |
| :----------------------- | :------------------ | :----------------------------------------------- |
| `URL`                    | `URL`               | 使用者提交的 YouTube 網址。                      |
| `Status`                 | `Select`            | 任務狀態，例如：`Pending`, `Processing`, `Completed`, `Failed` |
| `Title`                  | `Title`             | 影片標題 (可在處理後自動填入)。                  |
| `Summary`                | `Text`              | 生成的摘要內容。                                 |
| `Error Message`          | `Text`              | 如果處理失敗，記錄錯誤訊息。                     |
| `Created Time`           | `Created time`      | 任務建立時間。                                   |
| `Processed Time`         | `Last edited time`  | 任務最後處理時間。                               |

---

### **待辦事項清單 (To-Do List)**

根據以上分析，我將依序執行以下任務來完成您的需求：

1.  **環境設定:**
    *   在 `requirements.txt` 中新增必要的 Python 套件，主要為 `notion-client` (與 Notion API 互動) 和 `schedule` (用於排程)。

2.  **建立資料庫抽象層:**
    *   建立新檔案 `database_interface.py`，定義一個 `BaseDB` 抽象類別，包含 `add_task`, `get_pending_tasks`, `update_task_status` 等方法。

3.  **實現 Notion 資料庫連接器:**
    *   建立新檔案 `notion_client.py`，在其中實現 `NotionDB` 類別，繼承自 `BaseDB`。
    *   完成與 Notion API 的對接邏輯。
    *   這會需要您提供 Notion API Token 和 Database ID，我會將它們設定為環境變數，並更新 `.env.example` 檔案。

4.  **建立新的 Streamlit App:**
    *   建立 `scheduler_app.py` 檔案，並在其中編寫用於提交網址的介面。
    *   將提交邏輯與 `notion_client.py` 中的 `add_task` 方法對接。

5.  **建立排程器:**
    *   建立新檔案 `scheduler.py`。
    *   使用 `schedule` 套件設定定時任務，定期呼叫 Notion 客戶端獲取待處理任務。
    *   整合現有的 `main.py` 或相關模組的處理邏輯。

6.  **更新 Docker 設定:**
    *   修改 `docker-compose.yaml`，新增一個名為 `scheduler` 的 service，其 `command` 指向 `python scheduler.py`。
    *   確保 `scheduler` service 和 `streamlit` service 共享相同的環境變數設定 (env_file)。

7.  **建立測試:**
    *   為新的 `notion_client.py` 和 `scheduler.py` 的核心邏輯撰寫單元測試，確保其穩定性。
