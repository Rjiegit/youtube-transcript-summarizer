import re
import os

class FileManager:
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
        print(f"Saving text to {output_file}...")
        dir_path = 'data'
        santized_file = FileManager.sanitize_filename(output_file)
        # 截斷過長的檔名，但保持副檔名
        santized_file = FileManager.truncate_filename(santized_file)
        full_path = f"{dir_path}/{santized_file}"
        
        with open(full_path, "w", encoding="utf-8") as file:
            file.write(text)
            
        print(f"Text saved to {full_path}")

    @staticmethod
    def delete_file(file_path):
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"File {file_path} deleted.")
        else:
            print(f"File {file_path} not found.")