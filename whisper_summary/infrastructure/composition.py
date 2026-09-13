"""Composition root for concrete infrastructure adapters."""

from whisper_summary.core.config import Config
from whisper_summary.infrastructure.llm.summarizer_service import Summarizer
from whisper_summary.infrastructure.media.downloader import YouTubeDownloader
from whisper_summary.infrastructure.media.transcription.transcriber import Transcriber
from whisper_summary.infrastructure.notifications.discord import send_task_completion_notification
from whisper_summary.infrastructure.storage.file_storage import FileManager
from whisper_summary.infrastructure.storage.summary_storage import SummaryStorage
from whisper_summary.services.pipeline.dependencies import ProcessingDependencies


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
