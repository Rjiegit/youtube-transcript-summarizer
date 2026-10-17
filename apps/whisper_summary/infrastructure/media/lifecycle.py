"""POSIX media use protection and narrowly scoped, symlink-safe deletion."""

import fcntl
import os
import stat
from contextlib import contextmanager
from pathlib import Path

from whisper_summary.core.utils.url import extract_video_id


@contextmanager
def media_use_lock(data_dir: str | os.PathLike, url: str = "", *, blocking: bool = True):
    """Lock one video across URL aliases; unknown identities exclude all videos.

    Keep persistent lock inodes outside videos. A shared directory gate allows
    distinct videos to run concurrently; unknown URLs take its exclusive lock.
    Closing descriptors (including process exit) releases all acquired locks.
    """
    os.makedirs(data_dir, exist_ok=True)
    gate = os.open(os.path.join(data_dir, ".media-use.lock"), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    video_fd = None
    nonblocking = 0 if blocking else fcntl.LOCK_NB
    video_id = extract_video_id(url)
    try:
        fcntl.flock(gate, (fcntl.LOCK_SH if video_id else fcntl.LOCK_EX) | nonblocking)
        if video_id:
            # extract_video_id returns only the fixed-length safe YouTube ID.
            video_fd = os.open(
                os.path.join(data_dir, f".media-use-{video_id}.lock"),
                os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600,
            )
            fcntl.flock(video_fd, fcntl.LOCK_EX | nonblocking)
        yield
    finally:
        if video_fd is not None:
            os.close(video_fd)
        os.close(gate)


def delete_downloaded_media(file_path: str | os.PathLike, data_dir: str | os.PathLike) -> None:
    """Delete exactly one regular media file using no-follow directory descriptors."""
    root = Path(os.path.abspath(os.path.join(data_dir, "videos")))
    raw = Path(file_path)
    if ".." in raw.parts:
        raise ValueError("Media path contains parent traversal")
    path = Path(os.path.abspath(raw))
    relative = path.relative_to(root)
    media_extensions = {".mp3", ".mp4", ".m4a", ".webm", ".wav", ".ogg", ".mkv", ".mov", ".aac"}
    if not relative.parts or path.suffix.lower() not in media_extensions:
        raise ValueError("Not a downloaded media file")
    # Resolve only the configured data directory (e.g. macOS /var -> /private/var).
    # videos and all downloader-controlled components still use O_NOFOLLOW.
    fd = os.open(Path(data_dir).resolve(), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in ("videos", *relative.parts[:-1]):
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        info = os.stat(path.name, dir_fd=fd, follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("Media must be a regular file, not a symbolic link")
        # unlink never follows a replaced leaf symlink; the parent fd pins its directory.
        os.unlink(path.name, dir_fd=fd)
    except FileNotFoundError:
        pass
    finally:
        os.close(fd)
