import pytz
import os
import glob
from datetime import datetime
from transcriber import Transcriber
from summarizer import Summarizer
from file_manager import FileManager
from summary_storage import SummaryStorage

class Main:
    def __init__(self):
        self.timezone = pytz.timezone("Asia/Taipei")

    def run(self):
        start_time = datetime.now(self.timezone)
        print(f"Process started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        transcriber = Transcriber(model_size="tiny")
        summarizer = Summarizer()
        summary_storage = SummaryStorage()

        mp3_files = glob.glob("data/videos/*.mp3")
        mp4_files = glob.glob("data/videos/*.mp4")
        m4a_files = glob.glob("data/videos/*.m4a")
        files_to_process = mp3_files + mp4_files + m4a_files
        
        print(f"Total files to process: {len(files_to_process)}")
        
        for index, file_path in enumerate(files_to_process, start=1):
            print(f"Processing file {index}/{len(files_to_process)}: {file_path}")
            self.process_file(file_path, transcriber, summarizer, summary_storage)
            
        self.delete_zone_identifier_files()

        end_time = datetime.now(self.timezone)
        print(f"Process ended at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total time: {(end_time - start_time).total_seconds()} seconds")

    def process_file(self, file_path, transcriber, summarizer, summary_storage):
        try:
            start_time = datetime.now()  # 記錄開始時間
            file_title = os.path.splitext(os.path.basename(file_path))[0]
            print(f"Processing file: {file_title}")
            transcription_text = transcriber.transcribe(file_path)
            datetime_now = datetime.now().strftime('%Y%m%d%H%M%S')
            summarized_text = summarizer.summarize(file_title, transcription_text)
            
            FileManager.save_text(summarized_text, output_file=f"_summarized/{datetime_now}_{file_title}.md")
            summary_storage.save(
                title=file_title,
                text=summarized_text,
                model="",
                url=file_path
            )
            self.delete_file(file_path)
            
            end_time = datetime.now()  # 記錄結束時間
            processing_time = (end_time - start_time).total_seconds()
            print(f"Finished processing {file_title} in {processing_time:.2f} seconds")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            self.delete_file(file_path)

    def delete_file(self, file_path):
        try:
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

    def delete_zone_identifier_files(self):
        zone_files = glob.glob("data/videos/*Zone.Identifier")
        try:
            for file_path in zone_files:
                os.remove(file_path)
        except Exception as e:
            print(f"Error: {e}")
            
    def truncate_filename(filename, max_length=200):
        """
        截斷檔名，使其不超過指定的最大長度。
        """
        print(f"Truncating filename: {filename}")
        base_name, ext = os.path.splitext(filename)
        # 計算需要截斷的長度
        if len(base_name) + len(ext) > max_length:
            base_name = base_name[:max_length - len(ext)]
        # 返回截斷後的檔名
        return base_name + ext

if __name__ == "__main__":
    
    app = Main()
    
    try:
        app.run()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Process completed.")
        os._exit(0)
