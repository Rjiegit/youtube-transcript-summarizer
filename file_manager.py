import re
import os
import time
import random

try:
    import streamlit as st
except ImportError:
    st = None

try:
    from test_sample_manager import TestSampleManager
except ImportError:
    TestSampleManager = None

class FileManager:
    @staticmethod
    def _is_test_mode(text, output_file):
        """檢測是否為測試模式"""
        # 方法 1: 檢查 Streamlit session_state
        if st and hasattr(st, 'session_state') and st.session_state.get('test_mode', False):
            return True
        
        # 方法 2: 檢查檔案名中的測試標記
        if output_file and any(marker in output_file for marker in ['test_', 'mock_', '_test', '_mock']):
            return True
        
        # 方法 3: 檢查文字內容中的測試標記
        if text and any(marker in text for marker in ['[測試模式]', '[mock]', '[test]']):
            return True
            
        return False
    
    @staticmethod
    def _mock_save_text(text, output_file):
        """模擬檔案存儲過程"""
        print(f"[測試模式] 模擬存儲檔案: {output_file}")
        
        # 檢查 TestSampleManager 是否可用
        if TestSampleManager is None:
            print(f"[測試模式] TestSampleManager 不可用，使用基本模擬")
            time.sleep(random.uniform(0.1, 0.3))
            mock_path = f"mock_data/mock_{output_file}"
            print(f"[測試模式] 模擬檔案儲存完成: {mock_path}")
            return {"path": mock_path, "success": True, "size": len(text)}
        
        # 模擬處理時間
        time.sleep(random.uniform(0.1, 0.3))
        
        # 檢查是否要模擬錯誤
        sample_manager = TestSampleManager()
        if sample_manager.simulate_error():
            error_msg = sample_manager.get_random_error_message()
            print(f"[測試模式] 模擬檔案存儲錯誤: {error_msg}")
            raise Exception(f"[測試模式] {error_msg}")
        
        # 模擬檔案處理
        dir_path = 'mock_data'
        sanitized_file = FileManager.sanitize_filename(output_file)
        sanitized_file = FileManager.truncate_filename(sanitized_file)
        mock_path = f"{dir_path}/{sanitized_file}"
        
        print(f"[測試模式] 模擬檔案處理...")
        print(f"[測試模式] 原始檔名: {output_file}")
        print(f"[測試模式] 清理後檔名: {sanitized_file}")
        print(f"[測試模式] 模擬路徑: {mock_path}")
        print(f"[測試模式] 文字大小: {len(text)} 字元")
        print(f"[測試模式] 檔案儲存完成: {mock_path}")
        
        return {
            "path": mock_path,
            "success": True,
            "original_file": output_file,
            "sanitized_file": sanitized_file,
            "size": len(text),
            "text_preview": text[:100] + "..." if len(text) > 100 else text
        }

    @staticmethod
    def sanitize_filename(filename):
        return re.sub(r'[\\/:*?"<>|]', '_', filename)
    
    @staticmethod
    def truncate_filename(filename, max_length=200):
        """
        截斷檔名，使其不超過指定的最大長度，但保持副檔名不變
        Linux系統檔名限制通常是255 bytes，這裡設定為200以確保安全
        """
        if len(filename.encode('utf-8')) <= max_length:
            return filename
            
        # 分離檔名和副檔名
        base_name, ext = os.path.splitext(filename)
        ext_bytes = len(ext.encode('utf-8'))
        
        # 計算base_name可用的最大bytes數
        available_bytes = max_length - ext_bytes
        
        # 逐字截斷直到符合byte限制
        truncated_base = base_name
        while len(truncated_base.encode('utf-8')) > available_bytes and truncated_base:
            truncated_base = truncated_base[:-1]
        
        result = truncated_base + ext
        print(f"檔名過長，已截斷: {filename} -> {result}")
        return result
    
    @staticmethod
    def save_text(text, output_file):
        # 檢查是否為測試模式
        if FileManager._is_test_mode(text, output_file):
            return FileManager._mock_save_text(text, output_file)
        
        print(f"Saving text to {output_file}...")
        
        # Extract directory from output_file and create if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True) # exist_ok=True prevents error if dir already exists
            print(f"Created directory: {output_dir}")

        sanitized_file = FileManager.sanitize_filename(output_file)
        # 截斷過長的檔名，但保持副檔名
        sanitized_file = FileManager.truncate_filename(sanitized_file)
        full_path = os.path.join(output_dir, sanitized_file) # Use os.path.join for path construction
        
        with open(full_path, "w", encoding="utf-8") as file:
            file.write(text)
            
        print(f"Text saved to {full_path}")
        
        # 返回結果以保持一致性
        return {
            "path": full_path,
            "success": True,
            "original_file": output_file,
            "sanitized_file": sanitized_file,
            "size": len(text)
        }

    @staticmethod
    def delete_file(file_path):
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File {file_path} deleted.")
        else:
            print(f"File {file_path} not found.")