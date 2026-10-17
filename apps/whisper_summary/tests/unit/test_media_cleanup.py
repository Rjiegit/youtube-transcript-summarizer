import fcntl
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from whisper_summary.domain.tasks.leases import TaskLeaseLostError
from whisper_summary.domain.tasks.models import Task
from whisper_summary.tests.unit import test_processing_engines as fixtures


class TestMediaCleanup(unittest.TestCase):
    def test_engines_cleanup_only_after_success(self):
        for engine in ("legacy", "langgraph"):
            for failure in (None, "local", "publish", "local_false", "publish_false",
                            "transcribe", "lease", "notify", "delete", "missing", "disabled"):
                with self.subTest(engine=engine, failure=failure), tempfile.TemporaryDirectory() as directory:
                    from whisper_summary.services.pipeline.engines import create_processing_engine
                    runtime, _ = fixtures.TestProcessingEngineParity()._runtime()
                    runtime.config.data_dir = directory
                    runtime.config.delete_media_on_success = failure != "disabled"
                    media = Path(directory, "videos", "video.mp4")
                    media.parent.mkdir()
                    media.write_bytes(b"media")
                    sidecar = media.with_suffix(".metadata.json")
                    sidecar.write_text("{}")
                    runtime.downloader_factory("", "").download.side_effect = None
                    runtime.downloader_factory("", "").download.return_value = {"path": str(media), "title": "Title"}
                    if failure == "local":
                        runtime.file_manager_factory().save_text.side_effect = RuntimeError("save failed")
                    if failure == "publish":
                        runtime.summary_storage_factory().save.side_effect = RuntimeError("publish failed")
                    if failure == "local_false":
                        runtime.file_manager_factory().save_text.side_effect = None
                        runtime.file_manager_factory().save_text.return_value = {"success": False}
                    if failure == "publish_false":
                        runtime.summary_storage_factory().save.side_effect = None
                        runtime.summary_storage_factory().save.return_value = {"success": False, "page_id": "invalid"}
                    if failure == "transcribe":
                        runtime.transcriber_factory("").transcribe.side_effect = RuntimeError("transcription failed")
                    if failure == "lease":
                        runtime.db.update_task_status.side_effect = lambda _id, status, **kw: (
                            (_ for _ in ()).throw(TaskLeaseLostError("lost")) if status == "Completed" else None
                        )
                    if failure == "notify":
                        runtime = replace(runtime, notifier=lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("notify")))
                    if failure == "missing":
                        media.unlink()
                    task = Task(id="1", url="https://youtu.be/example", status="Processing")
                    if failure in ("local", "publish", "local_false", "publish_false", "transcribe", "lease"):
                        with self.assertRaises(TaskLeaseLostError if failure == "lease" else RuntimeError):
                            create_processing_engine(engine, runtime).execute(task)
                    elif failure == "delete":
                        with patch("whisper_summary.infrastructure.media.lifecycle.os.unlink", side_effect=PermissionError):
                            create_processing_engine(engine, runtime).execute(task)
                    else:
                        create_processing_engine(engine, runtime).execute(task)
                    retained = failure in {
                        "local", "publish", "local_false", "publish_false", "transcribe", "lease", "delete", "disabled",
                    }
                    self.assertEqual(media.exists(), retained)
                    self.assertTrue(sidecar.exists())
                    self.assertFalse(any(c.args[1] == "Failed" for c in runtime.db.update_task_status.call_args_list))

    def test_notification_failure_keeps_sqlite_completed(self):
        from whisper_summary.infrastructure.persistence.sqlite.client import SQLiteDB
        from whisper_summary.services.pipeline.dependencies import ProcessingDependencies
        from whisper_summary.services.pipeline.processing_runner import ProcessingWorker
        for engine in ("legacy", "langgraph"):
            with self.subTest(engine=engine), tempfile.TemporaryDirectory() as directory:
                db = SQLiteDB(db_path=str(Path(directory, "tasks.db")))
                db.add_task("https://youtu.be/example", processing_engine=engine)
                runtime, _ = fixtures.TestProcessingEngineParity()._runtime()
                runtime.config.data_dir = directory
                media = Path(directory, "videos", "video.mp4")
                media.parent.mkdir()
                media.touch()
                runtime.downloader_factory("", "").download.side_effect = None
                runtime.downloader_factory("", "").download.return_value = {"path": str(media), "title": "Title"}

                def failing_notification(*args, **kwargs):
                    self.assertEqual(db.get_all_tasks()[0].status, "Completed")
                    raise RuntimeError("Discord unavailable")

                dependencies = ProcessingDependencies(
                    downloader_factory=runtime.downloader_factory,
                    transcriber_factory=runtime.transcriber_factory,
                    summarizer_factory=runtime.summarizer_factory,
                    summary_storage_factory=runtime.summary_storage_factory,
                    file_manager_factory=runtime.file_manager_factory,
                    notifier=failing_notification,
                    config_factory=lambda: runtime.config,
                )
                summary = ProcessingWorker(db, dependencies=dependencies).run()
                self.assertEqual(summary.processed_tasks, 1)
                self.assertEqual(summary.failed_tasks, 0)
                self.assertEqual(db.get_all_tasks()[0].status, "Completed")
                self.assertFalse(media.exists())

    def test_missing_publication_confirmation_retains_media(self):
        from whisper_summary.services.pipeline.engines import create_processing_engine
        for engine in ("legacy", "langgraph"):
            with self.subTest(engine=engine), tempfile.TemporaryDirectory() as directory:
                runtime, _ = fixtures.TestProcessingEngineParity()._runtime()
                runtime.config.data_dir = directory
                media = Path(directory, "videos", "video.mp4")
                media.parent.mkdir()
                media.touch()
                runtime.downloader_factory("", "").download.side_effect = None
                runtime.downloader_factory("", "").download.return_value = {"path": str(media), "title": "Title"}
                runtime.summary_storage_factory().save.side_effect = None
                runtime.summary_storage_factory().save.return_value = None
                create_processing_engine(engine, runtime).execute(
                    Task(id="1", url="https://youtu.be/example", status="Processing", notion_page_id="old-page")
                )
                self.assertTrue(media.exists())

    def test_rejected_status_update_retains_media(self):
        from whisper_summary.services.pipeline.engines import create_processing_engine
        for engine in ("legacy", "langgraph"):
            for rejected in ("Processing", "Completed"):
                with self.subTest(engine=engine, rejected=rejected), tempfile.TemporaryDirectory() as directory:
                    runtime, _ = fixtures.TestProcessingEngineParity()._runtime()
                    runtime.config.data_dir = directory
                    media = Path(directory, "videos", "video.mp4")
                    media.parent.mkdir()
                    media.touch()
                    runtime.downloader_factory("", "").download.side_effect = None
                    runtime.downloader_factory("", "").download.return_value = {"path": str(media), "title": "Title"}
                    runtime.db.update_task_status.side_effect = lambda _id, status, **kw: status != rejected
                    with self.assertRaises(RuntimeError):
                        create_processing_engine(engine, runtime).execute(
                            Task(id="1", url="https://youtu.be/dQw4w9WgXcQ", status="Processing")
                        )
                    self.assertTrue(media.exists())
                    runtime.notifier.assert_not_called()

    def test_video_locks_allow_other_videos_but_block_aliases_and_unknown_urls(self):
        from whisper_summary.infrastructure.media.lifecycle import media_use_lock
        script = (
            "import sys; from whisper_summary.infrastructure.media.lifecycle import media_use_lock; "
            "lock = media_use_lock(sys.argv[1], sys.argv[2]); lock.__enter__(); "
            "print('locked', flush=True); sys.stdin.readline()"
        )
        with tempfile.TemporaryDirectory() as directory:
            child = subprocess.Popen(
                [sys.executable, "-c", script, directory, "https://youtu.be/dQw4w9WgXcQ"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
            )
            try:
                self.assertEqual(child.stdout.readline().strip(), "locked")
                for url, blocked in (("https://www.youtube.com/watch?v=dQw4w9WgXcQ", True),
                                     ("https://youtu.be/abcdefghijk", False), ("unknown", True)):
                    with self.subTest(url=url):
                        if blocked:
                            with self.assertRaises(BlockingIOError):
                                with media_use_lock(directory, url, blocking=False):
                                    pass
                        else:
                            with media_use_lock(directory, url, blocking=False):
                                pass
                child.kill()
                child.wait(timeout=10)
                with media_use_lock(directory, "https://youtu.be/dQw4w9WgXcQ", blocking=False):
                    pass
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=10)
                child.stdin.close()
                child.stdout.close()

    def test_configuration_default_and_opt_out(self):
        from whisper_summary.core.config import Config
        for value, expected in ((None, True), ("true", True), ("false", False), ("0", False)):
            env = {} if value is None else {"DELETE_MEDIA_ON_SUCCESS": value}
            with self.subTest(value=value), patch.dict(os.environ, env, clear=True):
                with patch("whisper_summary.core.config.load_dotenv"):
                    self.assertEqual(Config().delete_media_on_success, expected)

    def test_cross_process_lock_released_on_exit_and_crash(self):
        from whisper_summary.infrastructure.media.lifecycle import media_use_lock
        for crash in (False, True):
            with self.subTest(crash=crash), tempfile.TemporaryDirectory() as directory:
                script = (
                    "import sys; from whisper_summary.infrastructure.media.lifecycle import media_use_lock; "
                    "lock = media_use_lock(sys.argv[1]); lock.__enter__(); "
                    "print('locked', flush=True); sys.stdin.readline(); lock.__exit__(None, None, None)"
                )
                child = subprocess.Popen(
                    [sys.executable, "-c", script, directory],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                )
                try:
                    self.assertEqual(child.stdout.readline().strip(), "locked")
                    fd = os.open(Path(directory, ".media-use.lock"), os.O_RDWR)
                    try:
                        with self.assertRaises(BlockingIOError):
                            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    finally:
                        os.close(fd)
                    if crash:
                        child.kill()
                    else:
                        child.stdin.write("\n")
                        child.stdin.flush()
                    child.wait(timeout=10)
                    with media_use_lock(directory):
                        pass
                finally:
                    if child.poll() is None:
                        child.kill()
                        child.wait(timeout=10)
                    child.stdin.close()
                    child.stdout.close()

    def test_both_engines_hold_lock_through_download_read_and_cleanup(self):
        from whisper_summary.infrastructure.media.lifecycle import delete_downloaded_media
        from whisper_summary.services.pipeline.engines import create_processing_engine
        for engine in ("legacy", "langgraph"):
            with self.subTest(engine=engine), tempfile.TemporaryDirectory() as directory:
                runtime, _ = fixtures.TestProcessingEngineParity()._runtime()
                runtime.config.data_dir = directory
                media = Path(directory, "videos", "video.mp4")
                media.parent.mkdir()
                media.write_bytes(b"media")
                checked = []

                def check_lock():
                    fd = os.open(Path(directory, ".media-use-dQw4w9WgXcQ.lock"), os.O_RDWR)
                    try:
                        with self.assertRaises(BlockingIOError):
                            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        checked.append(True)
                    finally:
                        os.close(fd)

                def download():
                    check_lock()
                    return {"path": str(media), "title": "Title"}

                def transcribe(_path):
                    check_lock()
                    self.assertTrue(media.exists())
                    return "transcript"

                def cleanup(*args):
                    check_lock()
                    self.assertEqual(runtime.db.update_task_status.call_args.args[1], "Completed")
                    delete_downloaded_media(*args)

                runtime.downloader_factory("", "").download.side_effect = download
                runtime.transcriber_factory("").transcribe.side_effect = transcribe
                with patch("whisper_summary.services.pipeline.engines.delete_downloaded_media", side_effect=cleanup):
                    create_processing_engine(engine, runtime).execute(
                        Task(id="1", url="https://youtu.be/dQw4w9WgXcQ", status="Processing")
                    )
                self.assertEqual(len(checked), 3)
                self.assertFalse(media.exists())

    def test_rejects_unsafe_paths(self):
        from whisper_summary.infrastructure.media.lifecycle import delete_downloaded_media
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory, "videos")
            root.mkdir()
            outside = Path(directory, "outside.mp4")
            outside.write_bytes(b"keep")
            link = root / "link.mp4"
            link.symlink_to(outside)
            nested = root / "nested"
            nested.symlink_to(Path(directory), target_is_directory=True)
            for path in (outside, link, nested / outside.name, root / ".." / outside.name):
                with self.subTest(path=path), self.assertRaises((ValueError, OSError)):
                    delete_downloaded_media(path, directory)
            self.assertTrue(outside.exists())
            self.assertTrue(link.is_symlink())
            for name in ("summary.txt", "video.metadata.json", "tasks.sqlite", "model.bin"):
                protected = root / name
                protected.touch()
                with self.assertRaises(ValueError):
                    delete_downloaded_media(protected, directory)
                self.assertTrue(protected.exists())
            link.unlink()
            nested.unlink()
            # Reject even an in-root target: symbolic links are never cleanup candidates.
            target = root / "target.mp4"
            target.touch()
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                delete_downloaded_media(link, directory)
            self.assertTrue(target.exists())
            link.unlink()
            moved = Path(directory, "real-videos")
            root.rename(moved)
            root.symlink_to(moved, target_is_directory=True)
            with self.assertRaises(OSError):
                delete_downloaded_media(root / "target.mp4", directory)
            self.assertTrue((moved / "target.mp4").exists())


if __name__ == "__main__":
    unittest.main()
