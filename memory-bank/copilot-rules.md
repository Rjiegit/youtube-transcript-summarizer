# Copilot Rules

## 🚨 安全規則

### API 金鑰管理
- **絕不提交機密**: 永遠不要將 API 金鑰、`.env` 檔案或任何敏感資訊提交到版本控制
- **使用範例檔案**: 維護 `.env.example` 檔案，僅包含安全的佔位符值
- **洩漏處理**: 如果機密被意外提交，立即視為安全事件：
  1. 更換受影響的憑證
  2. 從 Git 歷史中清除
  3. 通知團隊
  4. 使用工具掃描 (GitHub Secret Scanning, TruffleHog)

### API 金鑰清單
```env
# 需要保護的敏感資訊
OPENAI_API_KEY=          # OpenAI API 金鑰
GOOGLE_GEMINI_API_KEY=   # Google Gemini API 金鑰
NOTION_API_KEY=          # Notion 整合金鑰
NOTION_DATABASE_ID=      # Notion 資料庫 ID
```

## 🏗️ 開發模式

### 程式碼結構原則
1. **單一職責**: 每個類別/函數專注於一個特定功能
2. **依賴注入**: 避免硬編碼依賴，使用參數傳遞
3. **錯誤處理**: 所有外部調用都要有適當的錯誤處理
4. **資源清理**: 檔案和網路資源使用後要正確釋放

### 檔案命名規範
- **Python 檔案**: 使用小寫和底線 (`file_manager.py`)
- **測試檔案**: 前綴 `test_` (`test_file_manager.py`)
- **設定檔案**: 清晰的副檔名 (`.env`, `.example`)
- **輸出檔案**: 時間戳前綴 (`_summarized_20250819_title.md`)

### 模組設計原則
```python
# 標準模組結構
class ModuleName:
    def __init__(self, config):
        """初始化時接收設定"""
        
    def main_function(self, input_data):
        """主要功能，返回處理結果"""
        try:
            # 主要處理邏輯
            return result
        except SpecificException as e:
            # 具體錯誤處理
            logger.error(f"Error in {self.__class__.__name__}: {e}")
            raise
        finally:
            # 資源清理
            pass
```

## 🧪 測試規範

### 測試覆蓋要求
- **核心功能**: 必須有單元測試
- **整合點**: 需要整合測試
- **錯誤路徑**: 錯誤情況也要測試
- **邊界條件**: 極值和邊界情況測試

### 測試檔案結構
```python
import unittest
from unittest.mock import Mock, patch

class TestModuleName(unittest.TestCase):
    def setUp(self):
        """測試前置設定"""
        
    def test_normal_case(self):
        """測試正常情況"""
        
    def test_error_case(self):
        """測試錯誤情況"""
        
    def tearDown(self):
        """測試後清理"""
```

## 📝 文件維護

### Docstring 標準
```python
def function_name(param1: str, param2: int) -> str:
    """
    簡要描述函數功能。
    
    Args:
        param1: 參數1的描述
        param2: 參數2的描述
        
    Returns:
        返回值的描述
        
    Raises:
        SpecificException: 特定錯誤條件
    """
```

### 註解原則
- **中文註解**: 使用繁體中文註解
- **技術術語**: 保留英文技術術語
- **複雜邏輯**: 解釋為什麼，不只是做什麼
- **TODO 標記**: 使用 `# TODO:` 標記待辦事項

## 🔧 效能考量

### 資源管理
- **記憶體**: 大檔案使用串流處理
- **磁碟**: 及時清理暫存檔案
- **網路**: 實施重試和超時機制
- **CPU**: 考慮並行處理的可能性

### 最佳化原則
1. **先測量後優化**: 不要過早優化
2. **瓶頸識別**: 專注於真正的效能瓶頸
3. **可讀性優先**: 效能優化不能犧牲可讀性
4. **分段處理**: 大任務分解為小步驟

## 🐛 除錯指南

### 日誌等級
- **INFO**: 正常處理流程
- **WARNING**: 潛在問題，但可繼續
- **ERROR**: 錯誤情況，需要注意
- **DEBUG**: 詳細的除錯資訊（開發時使用）

### 錯誤分類
```python
# 錯誤處理模式
try:
    # 危險操作
    result = risky_operation()
except NetworkError as e:
    # 網路相關錯誤
    logger.warning(f"Network issue: {e}")
    # 重試邏輯
except ValidationError as e:
    # 資料驗證錯誤
    logger.error(f"Invalid data: {e}")
    # 清理和回報
except Exception as e:
    # 未預期的錯誤
    logger.error(f"Unexpected error: {e}")
    # 緊急處理
```

## 🚀 部署注意事項

### Docker 最佳實踐
- **分層構建**: 依賴和應用程式分層
- **最小化映像**: 僅包含必要組件
- **環境隔離**: 開發/測試/生產環境分離
- **健康檢查**: 容器健康狀態監控

### 環境變數管理
```bash
# 生產環境檢查清單
- [ ] 所有必要的環境變數都已設定
- [ ] API 金鑰具有適當的權限範圍
- [ ] 檔案權限設定正確
- [ ] 網路連接測試通過
- [ ] 磁碟空間充足
```

---

**記住**: 這些規則是活的文件，隨著專案發展持續更新。優先考慮安全性、可維護性和使用者體驗。
