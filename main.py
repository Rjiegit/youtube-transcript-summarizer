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
        transcriber = Transcriber(model="base")
        summarizer = Summarizer()
        summary_storage = SummaryStorage()

        # Process all mp4 files in data/videos folder
        video_files = glob.glob("data/videos/*.mp4")
        for file_path in video_files:
            file_title = os.path.basename(file_path).split('.')[0]
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
            
            datetime_now = datetime.now().strftime('%Y%m%d%H%M%S')
            summarized_text = summarizer.summarize(file_title, transcription_text)
            FileManager.save_text(summarized_text, output_file=f"_summarized/{datetime_now}_{file_title}.md")
            summary_storage.save(
                title=file_title,
                text=summarized_text,
                model="",
                url=file_path
            )

        end_time = datetime.now(self.timezone)
        print(f"Process ended at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total time: {(end_time - start_time).total_seconds()} seconds")
    
        FileManager.delete_file(file_path)

if __name__ == "__main__":
    
    app = Main()
    
    try:
        app.run()
    except Exception as e:
        print(f"Error: {e}")