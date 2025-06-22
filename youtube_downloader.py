from pytubefix import YouTube
from pytubefix.cli import on_progress
import os
from logger import logger
import subprocess

class YouTubeDownloader:
    def __init__(self, url, output_path="data"):
        self.url = url
        self.output_path = output_path
    
    def download(self):
        # Always use yt-dlp for download
        logger.info(f"Download YouTube video using yt-dlp...")
        return self._download_with_yt_dlp()

    def _download_with_yt_dlp(self):
        output_dir = os.path.join(self.output_path, "videos")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        cmd = [
            "yt-dlp",
            "-S", "res:360",
            "-o", os.path.join(output_dir, '%(title)s.%(ext)s'),
            self.url
        ]
        subprocess.run(cmd, check=True)
        # Find the latest downloaded video file (any extension)
        files = [f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))]
        if not files:
            raise Exception("yt-dlp did not download any video file.")
        latest_file = max([os.path.join(output_dir, f) for f in files], key=os.path.getctime)
        title = os.path.splitext(os.path.basename(latest_file))[0]
        return {"path": latest_file, "title": title}

    def _download_with_pytube(self):
        yt = YouTube(self.url, on_progress_callback=on_progress)
        video = yt.streams.filter(only_audio=True).first()
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        video_path = video.download(output_path=self.output_path)
        logger.info(f"Downloaded file path: {video_path}, title: {yt.title}")
        return {"path": video_path, "title": yt.title}