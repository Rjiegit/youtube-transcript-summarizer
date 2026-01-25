import glob
import os
import subprocess
from typing import Optional

from src.core.logger import logger
from src.core.utils.url import extract_video_id


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

        def _truncate(text: Optional[str], limit: int = 800) -> str:
            if not text:
                return ""
            normalized = str(text).replace("\r", "")
            if len(normalized) <= limit:
                return normalized
            return normalized[:limit] + "...(truncated)"

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
        title: Optional[str] = None
        try:
            proc = subprocess.run(
                cmd, check=True, capture_output=True, text=True
            )
            if (proc.stderr or "").strip():
                logger.warning(f"yt-dlp stderr: {_truncate(proc.stderr.strip())}")

            lines = [l.strip() for l in proc.stdout.splitlines() if l.strip()]
            if len(lines) >= 1:
                path = lines[0]
                logger.info(f"yt-dlp returned path={path}")
            if len(lines) >= 2:
                title = lines[1]
                logger.info(f"yt-dlp returned title={title}")
            if len(lines) > 2:
                logger.warning(
                    f"yt-dlp returned unexpected extra stdout lines: count={len(lines)} preview={_truncate(proc.stdout)}"
                )
        except subprocess.CalledProcessError as e:
            logger.error(
                "yt-dlp failed. "
                f"returncode={e.returncode} "
                f"stdout={_truncate(e.stdout)} "
                f"stderr={_truncate(e.stderr)}"
            )
            lines = [l.strip() for l in (e.stdout or "").splitlines() if l.strip()]
            if len(lines) >= 1 and not path:
                path = lines[0]
                logger.info(f"yt-dlp (error) still returned path={path}")
            if len(lines) >= 2 and not title:
                title = lines[1]
                logger.info(f"yt-dlp (error) still returned title={title}")
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

        if not title:
            # Fallback: query the title independently (may require network access).
            try:
                tproc = subprocess.run(
                    ["yt-dlp", "-O", "%(title)s", self.url],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                if (tproc.stderr or "").strip():
                    logger.warning(f"yt-dlp -O stderr: {_truncate(tproc.stderr.strip())}")
                title = (tproc.stdout or "").strip()
                logger.info(f"Resolved title via -O: {title}")
            except subprocess.CalledProcessError as e:
                logger.error(
                    "yt-dlp -O title lookup failed. "
                    f"returncode={e.returncode} "
                    f"stdout={_truncate(e.stdout)} "
                    f"stderr={_truncate(e.stderr)}"
                )
                title = "(unknown title)"
            except Exception as e:
                logger.error(f"yt-dlp -O title lookup errored: {e}")
                title = "(unknown title)"

        logger.info(f"Download result: path={path}, title={title}")
        return {"path": path, "title": title}
