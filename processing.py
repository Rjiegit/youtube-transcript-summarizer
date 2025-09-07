import os
from database.db_factory import DBFactory
import time
from database.database_interface import BaseDB
from database.task import Task
from transcriber import Transcriber
from summarizer import Summarizer
from youtube_downloader import YouTubeDownloader
from file_manager import FileManager
from summary_storage import SummaryStorage
from logger import logger
import os
from config import Config
from url_validator import extract_video_id


def build_summary_output_path(title: str, url: str, now: float | None = None) -> str:
    """Build a unique output path for the summary file.

    Pattern: data/summaries/_summarized_YYYYMMDDHHMMSS_<videoId|noid>_<sanitized_title>.md

    Args:
        title: Video title to include in filename (sanitized later).
        url: The YouTube URL; used to extract videoId.
        now: Optional epoch seconds to freeze timestamp (for testing).

    Returns:
        The target path under data/summaries/.
    """
    ts = time.strftime(
        "%Y%m%d%H%M%S", time.localtime(now) if now is not None else time.localtime()
    )
    video_id = extract_video_id(url) or "noid"
    sanitized_title = FileManager.sanitize_filename(title or "untitled")
    filename = f"_summarized_{ts}_{video_id}_{sanitized_title}.md"
    return os.path.join("data", "summaries", filename)


def get_db_client():
    """Gets the database client based on the environment variable."""
    db_type = os.environ.get("DB_TYPE", "sqlite").lower()
    logger.info(f"Using {db_type} database.")
    return DBFactory.get_db(db_type)


def _process_task(task: Task, db: BaseDB):
    logger.info(f"Processing task: {task.url}")
    start_time = time.time()  # Record start time
    try:
        # Update task status to Processing
        db.update_task_status(task.id, "Processing", title=task.title)

        # Download video
        downloader = YouTubeDownloader(task.url, output_path="data")
        result = downloader.download()
        file_path = result["path"]
        task.title = result["title"]  # Update task title from download result

        # Transcribe (use model size from Config)
        cfg = Config()
        transcriber = Transcriber(model_size=cfg.transcription_model_size)
        transcription_text = transcriber.transcribe(file_path)

        # Summarize
        summarizer = Summarizer()
        summarized_text = summarizer.summarize(task.title, transcription_text)

        # Determine model label dynamically from Summarizer
        summarizer_label = getattr(summarizer, "last_model_label", "unknown")
        model_label = f"faster-whisper-{cfg.transcription_model_size}+{summarizer_label}"

        # Save summary to file (unique filename)
        output_file = build_summary_output_path(task.title, task.url)
        FileManager.save_text(summarized_text, output_file)

        # Save summary to storage (e.g., Notion)
        summary_storage = SummaryStorage()
        summary_storage.save(
            title=task.title,
            text=summarized_text,
            model=model_label,
            url=task.url,
        )

        end_time = time.time()  # Record end time
        duration = end_time - start_time
        # Update task status to Completed
        db.update_task_status(
            task.id,
            "Completed",
            title=task.title,
            summary=summarized_text,
            processing_duration=duration,
        )
        logger.info(f"Task {task.id} completed in {duration:.2f} seconds.")

    except Exception as e:
        end_time = time.time()  # Record end time even on failure
        duration = end_time - start_time
        logger.error(f"Error processing task {task.id}: {e}")
        db.update_task_status(
            task.id, "Failed", error_message=str(e), processing_duration=duration
        )


def process_pending_tasks():
    """Processes all pending tasks in the database."""
    db = get_db_client()
    pending_tasks = db.get_pending_tasks()
    logger.info(f"Found {len(pending_tasks)} pending tasks.")

    if not pending_tasks:
        return

    for task in pending_tasks:
        _process_task(task, db)
