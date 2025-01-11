import re
import os

class FileManager:
    @staticmethod
    def sanitize_filename(filename):
        return re.sub(r'[\\/:*?"<>|]', '_', filename)
    
    @staticmethod
    def save_text(text, output_file):
        print(f"Saving text to {output_file}...")
        dir_path = 'data'
        santized_file = FileManager.sanitize_filename(output_file)
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