import argparse
from datetime import datetime
import pytz
from youtube_downloader import YouTubeDownloader
from transcriber import Transcriber
from summarizer import Summarizer
from file_manager import FileManager

class Main:
    def __init__(self, youtube_url):
        self.youtube_url = youtube_url
        self.timezone = pytz.timezone("Asia/Taipei")
    
    def run(self):
        start_time = datetime.now(self.timezone)
        print(f"Process started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        downloader = YouTubeDownloader(self.youtube_url)
        transcriber = Transcriber(model="base")
        summarizer = Summarizer()
        
        download_result = downloader.download()
        file_path = download_result["path"]
        file_title = download_result["title"]
        
        transcription_text = transcriber.transcribe(file_path)
        FileManager.save_text(transcription_text, output_file=f"{file_title}_transcription.txt")
        
        summarized_text = summarizer.summarize(transcription_text)
        FileManager.save_text(summarized_text, output_file=f"{file_title}_summary.md")
        
        end_time = datetime.now(self.timezone)
        print(f"Process ended at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total time: {(end_time - start_time).total_seconds()} seconds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download YouTube video and transcribe subtitles")
    parser.add_argument("youtube_url", type=str, help="YouTube video URL")
    args = parser.parse_args()
    
    app = Main(args.youtube_url)
    try:
        app.run()
    except Exception as e:
        print(f"Error: {e}")