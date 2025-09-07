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

        # Transcribe
        transcriber = Transcriber()
        transcription_text = transcriber.transcribe(file_path)

        # Summarize
        summarizer = Summarizer()
        summarized_text = summarizer.summarize(task.title, transcription_text)

        # Save summary to file
        sanitized_title = FileManager.sanitize_filename(task.title)
        output_file = f"data/summaries/{sanitized_title}.md"
        FileManager.save_text(summarized_text, output_file)

        # Save summary to storage (e.g., Notion)
        summary_storage = SummaryStorage()
        summary_storage.save(
            title=task.title,
            text=summarized_text,
            model="whisper-openai",  # Assuming a model name
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


def process_pending_tasks(db_type: str | None = None):
    """Processes all pending tasks in the database.

    If db_type is provided, it will be used to select the database; otherwise,
    the environment variable DB_TYPE (default sqlite) is used.
    """
    db = DBFactory.get_db(db_type) if db_type else get_db_client()
    pending_tasks = db.get_pending_tasks()
    logger.info(f"Found {len(pending_tasks)} pending tasks.")

    if not pending_tasks:
        return

    for task in pending_tasks:
        _process_task(task, db)
