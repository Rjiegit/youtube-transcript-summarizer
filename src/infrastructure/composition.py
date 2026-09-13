"""Composition root for concrete infrastructure adapters."""

from src.core.config import Config
from src.infrastructure.llm.summarizer_service import Summarizer
from src.infrastructure.media.downloader import YouTubeDownloader
from src.infrastructure.media.transcription.transcriber import Transcriber
from src.infrastructure.notifications.discord import send_task_completion_notification
from src.infrastructure.storage.file_storage import FileManager
from src.infrastructure.storage.summary_storage import SummaryStorage
from src.services.pipeline.dependencies import ProcessingDependencies


def create_processing_dependencies() -> ProcessingDependencies:
    return ProcessingDependencies(
        downloader_factory=lambda url, output_path: YouTubeDownloader(url, output_path=output_path),
        transcriber_factory=lambda model_size: Transcriber(model_size=model_size),
        summarizer_factory=Summarizer,
        summary_storage_factory=SummaryStorage,
        file_manager_factory=FileManager,
        notifier=send_task_completion_notification,
        config_factory=Config,
    )
