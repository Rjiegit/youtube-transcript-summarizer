
import os
from db.db_factory import DBFactory
from youtube_downloader import YouTubeDownloader
from transcriber import Transcriber
from summarizer import Summarizer
from logger import logger
from db.task import Task

def get_db_client():
    """Gets the database client based on the environment variable."""
    db_type = os.environ.get("DB_TYPE", "sqlite").lower()
    logger.info(f"Using {db_type} database.")
    return DBFactory.get_db(db_type)

def process_task(db, task: Task):
    """Processes a single task."""
    logger.info(f"Processing task {task.id}: {task.url}")

    try:
        # Download
        downloader = YouTubeDownloader(task.url)
        video_info = downloader.download()
        video_path = video_info["path"]
        video_title = video_info["title"]

        # Transcribe
        transcriber = Transcriber(model_size="tiny")
        transcription_text = transcriber.transcribe(video_path)

        # Summarize
        summarizer = Summarizer()
        summarized_text = summarizer.summarize(video_title, transcription_text)

        # Update DB
        db.update_task_status(task.id, "Completed", summary=summarized_text)
        logger.info(f"Successfully processed task {task.id}")

    except Exception as e:
        logger.error(f"Error processing task {task.id}: {e}")
        db.update_task_status(task.id, "Failed", error_message=str(e))

    finally:
        # Clean up downloaded file
        if 'video_path' in locals() and os.path.exists(video_path):
            os.remove(video_path)
            logger.info(f"Deleted video file: {video_path}")

def process_pending_tasks():
    """Processes all pending tasks in the database."""
    db = get_db_client()
    pending_tasks = db.get_pending_tasks()
    logger.info(f"Found {len(pending_tasks)} pending tasks.")

    if not pending_tasks:
        return

    for task in pending_tasks:
        process_task(db, task)
