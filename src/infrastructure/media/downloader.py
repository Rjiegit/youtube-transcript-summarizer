import glob
import json
import os
import subprocess
from typing import Optional

from src.core.logger import logger
from src.core.utils.url import extract_video_id
from src.domain.media.models import VideoMetadata


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
        path_prefix = "__YT_DLP_PATH__="
        title_prefix = "__YT_DLP_TITLE__="
        metadata_prefix = "__YT_DLP_METADATA__="

        def _truncate(text: Optional[str], limit: int = 800) -> str:
            if not text:
                return ""
            normalized = str(text).replace("\r", "")
            if len(normalized) <= limit:
                return normalized
            return normalized[:limit] + "...(truncated)"

        def _parse_print_lines(
            lines: list[str],
        ) -> tuple[Optional[str], Optional[str], Optional[dict]]:
            found_path = None
            found_title = None
            found_metadata = None
            for line in lines:
                if line.startswith(path_prefix):
                    found_path = line[len(path_prefix):].strip()
                elif line.startswith(title_prefix):
                    found_title = line[len(title_prefix):].strip()
                elif line.startswith(metadata_prefix):
                    try:
                        parsed = json.loads(line[len(metadata_prefix):])
                        if isinstance(parsed, dict):
                            found_metadata = parsed
                    except (TypeError, json.JSONDecodeError) as exc:
                        logger.warning(f"Could not parse yt-dlp metadata JSON: {exc}")
            if (
                found_path is not None
                or found_title is not None
                or found_metadata is not None
            ):
                return found_path, found_title, found_metadata
            fallback_path = lines[0] if len(lines) >= 1 else None
            fallback_title = lines[1] if len(lines) >= 2 else None
            return fallback_path, fallback_title, None

        def _looks_like_filepath(value: str, expected_path: Optional[str]) -> bool:
            if not value:
                return False
            if expected_path and os.path.normpath(value) == os.path.normpath(expected_path):
                return True
            if os.path.isabs(value) and os.path.splitext(value)[1]:
                return True
            return os.path.isfile(value)

        cmd = [
            "yt-dlp",
            "--no-overwrites",
            "-S",
            "res:360",
            "-o",
            template,
            "--print",
            f"after_move:{path_prefix}%(filepath)s",
            "--print",
            f"{title_prefix}%(title)s",
            "--print",
            (
                f"{metadata_prefix}"
                "%(.{id,title,description,channel,channel_id,upload_date,"
                "duration,chapters})+j"
            ),
            self.url,
        ]
        logger.info(
            f"Running yt-dlp with deterministic template. url={self.url}, id={video_id}"
        )

        path = None
        title: Optional[str] = None
        raw_metadata: Optional[dict] = None
        try:
            proc = subprocess.run(
                cmd, check=True, capture_output=True, text=True
            )
            if (proc.stderr or "").strip():
                logger.warning(f"yt-dlp stderr: {_truncate(proc.stderr.strip())}")

            lines = [l.strip() for l in proc.stdout.splitlines() if l.strip()]
            path, title, raw_metadata = _parse_print_lines(lines)
            if path:
                logger.info(f"yt-dlp returned path={path}")
            if title:
                logger.info(f"yt-dlp returned title={title}")
            if any(
                line
                for line in lines
                if not line.startswith(path_prefix)
                and not line.startswith(title_prefix)
                and not line.startswith(metadata_prefix)
            ):
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
            parsed_path, parsed_title, parsed_metadata = _parse_print_lines(lines)
            if parsed_path and not path:
                path = parsed_path
                logger.info(f"yt-dlp (error) still returned path={path}")
            if parsed_title and not title:
                title = parsed_title
                logger.info(f"yt-dlp (error) still returned title={title}")
            if parsed_metadata and not raw_metadata:
                raw_metadata = parsed_metadata
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

        if title and _looks_like_filepath(title, path):
            logger.warning(
                f"yt-dlp title looked like a filepath, ignoring it. title={title}"
            )
            title = None

        if not title and raw_metadata:
            metadata_title = raw_metadata.get("title")
            if isinstance(metadata_title, str) and metadata_title.strip():
                title = metadata_title.strip()

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

        metadata = VideoMetadata.from_info_dict(
            raw_metadata or {},
            source_url=self.url,
            fallback_video_id=video_id,
            fallback_title=title,
        )
        logger.info(f"Download result: path={path}, title={title}")
        return {"path": path, "title": title, "metadata": metadata}
