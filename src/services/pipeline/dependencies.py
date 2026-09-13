"""Dependency bundle required by the processing application service."""

from dataclasses import dataclass
from typing import Callable, Protocol

from src.core.config import Config


class Downloader(Protocol):
    def download(self) -> dict: ...


class Transcriber(Protocol):
    def transcribe(self, file_path: str) -> str: ...


class Summarizer(Protocol):
    last_model_label: str | None

    def summarize(self, title: str, text: str, metadata=None) -> str: ...


class SummaryStorage(Protocol):
    def save(self, *, title: str, text: str, model: str, url: str): ...


class FileManager(Protocol):
    def save_text(self, text: str, output_file: str): ...

    def save_json(self, data: dict, output_file: str): ...


@dataclass(frozen=True)
class ProcessingDependencies:
    downloader_factory: Callable[[str, str], Downloader]
    transcriber_factory: Callable[[str], Transcriber]
    summarizer_factory: Callable[[], Summarizer]
    summary_storage_factory: Callable[[], SummaryStorage]
    file_manager_factory: Callable[[], FileManager]
    notifier: Callable[..., bool]
    config_factory: Callable[[], Config]
