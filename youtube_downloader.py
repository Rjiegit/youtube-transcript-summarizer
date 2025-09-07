import os
from logger import logger
import subprocess
from typing import Dict, Any
import glob
from url_validator import extract_video_id


class YouTubeDownloader:
    def __init__(self, url, output_path="data"):
        self.url = url
        self.output_path = output_path

    def download(self):
        # Always use yt-dlp for download（移除測試模式與模擬下載邏輯）
        logger.info("Download YouTube video using yt-dlp...")
        return self._download_with_yt_dlp()

    def _download_with_yt_dlp(self):
        output_dir = os.path.join(self.output_path, "videos")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        # Prefer deterministic filename by video id and read back via --print
        video_id = extract_video_id(self.url)
        template = os.path.join(output_dir, "%(id)s.%(ext)s")

        cmd = [
            "yt-dlp",
            "--no-overwrites",
            "-S",
            "res:360",
            "-o",
            template,
            "--print",
            "after_move:filepath",
            "--print",
            "title",
            self.url,
        ]
        logger.info(
            f"Running yt-dlp with deterministic template. url={self.url}, id={video_id}"
        )

        path = None
        title = None
        try:
            proc = subprocess.run(
                cmd, check=True, capture_output=True, text=True
            )
            lines = [l.strip() for l in proc.stdout.splitlines() if l.strip()]
            if len(lines) >= 1:
                path = lines[0]
                logger.info(f"yt-dlp returned path={path}")
        except Exception as e:
            logger.warning(f"yt-dlp --print parsing failed, will fallback. err={e}")

        # Fallback to glob by video id if path is not obtained or file missing
        if (not path or not os.path.isfile(path)) and video_id:
            candidates = glob.glob(os.path.join(output_dir, f"{video_id}.*"))
            if candidates:
                # pick the most recent candidate
                path = max(candidates, key=os.path.getctime)
                logger.info(f"Resolved path via glob: {path}")

        if not path or not os.path.isfile(path):
            # As a last resort, error out clearly
            raise Exception("yt-dlp did not produce an output file for this URL")

        # Always query the title independently to avoid mixing with filepath output
        try:
            tproc = subprocess.run(
                ["yt-dlp", "-O", "%(title)s", self.url],
                check=True,
                capture_output=True,
                text=True,
            )
            title = (tproc.stdout or "").strip()
            logger.info(f"Resolved title via -O: {title}")
        except Exception:
            title = "(unknown title)"

        return {"path": path, "title": title}

