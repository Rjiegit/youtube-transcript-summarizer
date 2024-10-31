from pytubefix import YouTube
from pytubefix.cli import on_progress
import os

class YouTubeDownloader:
    def __init__(self, url, output_path="data"):
        self.url = url
        self.output_path = output_path
    
    def download(self):
        print(f"Download YouTube video...")
        yt = YouTube(self.url, on_progress_callback=on_progress)
        video = yt.streams.filter(only_audio=True).first()
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        video_path = video.download(output_path=self.output_path)
        return {"path": video_path, "title": yt.title}