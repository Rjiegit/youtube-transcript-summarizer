from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class VideoChapter:
    title: str
    start_time: float
    end_time: float | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }


@dataclass(frozen=True)
class VideoMetadata:
    video_id: str | None
    source_url: str
    title: str
    description: str | None = None
    channel: str | None = None
    channel_id: str | None = None
    upload_date: str | None = None
    duration_seconds: float | None = None
    chapters: tuple[VideoChapter, ...] = field(default_factory=tuple)
    extracted_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    schema_version: int = 1

    @classmethod
    def from_info_dict(
        cls,
        info: dict[str, Any],
        *,
        source_url: str,
        fallback_video_id: str | None = None,
        fallback_title: str = "",
    ) -> "VideoMetadata":
        raw_chapters = info.get("chapters")
        chapters = []
        if isinstance(raw_chapters, list):
            for raw_chapter in raw_chapters:
                if not isinstance(raw_chapter, dict):
                    continue
                chapter = cls._parse_chapter(raw_chapter)
                if chapter is not None:
                    chapters.append(chapter)

        return cls(
            video_id=cls._optional_string(info.get("id")) or fallback_video_id,
            source_url=source_url,
            title=cls._optional_string(info.get("title")) or fallback_title,
            description=cls._optional_string(info.get("description")),
            channel=cls._optional_string(info.get("channel")),
            channel_id=cls._optional_string(info.get("channel_id")),
            upload_date=cls._normalize_upload_date(info.get("upload_date")),
            duration_seconds=cls._optional_number(info.get("duration")),
            chapters=tuple(chapters),
        )

    @staticmethod
    def _parse_chapter(raw: dict[str, Any]) -> VideoChapter | None:
        title = VideoMetadata._optional_string(raw.get("title"))
        start_time = VideoMetadata._optional_number(raw.get("start_time"))
        if not title or start_time is None:
            return None
        return VideoChapter(
            title=title,
            start_time=start_time,
            end_time=VideoMetadata._optional_number(raw.get("end_time")),
        )

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        return value.strip() if isinstance(value, str) and value.strip() else None

    @staticmethod
    def _optional_number(value: Any) -> float | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return float(value)

    @staticmethod
    def _normalize_upload_date(value: Any) -> str | None:
        normalized = VideoMetadata._optional_string(value)
        if not normalized:
            return None
        if len(normalized) == 8 and normalized.isdigit():
            return f"{normalized[:4]}-{normalized[4:6]}-{normalized[6:]}"
        return normalized

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "source_url": self.source_url,
            "video_id": self.video_id,
            "title": self.title,
            "description": self.description,
            "channel": self.channel,
            "channel_id": self.channel_id,
            "upload_date": self.upload_date,
            "duration_seconds": self.duration_seconds,
            "chapters": [chapter.to_dict() for chapter in self.chapters],
            "extracted_at": self.extracted_at,
        }
