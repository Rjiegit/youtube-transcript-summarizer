from datetime import datetime, timezone, timedelta

from src.domain.tasks.models import Task


def build_task(
    *,
    id: str,
    url: str = "https://youtu.be/example",
    status: str = "Completed",
    title: str = "Example",
    created_offset_minutes: int = 0,
    processing_duration: float | None = None,
    notion_page_id: str | None = None,
    notion_url: str | None = None,
) -> Task:
    created_at = datetime.now(tz=timezone.utc) - timedelta(minutes=created_offset_minutes)
    return Task(
        id=id,
        url=url,
        status=status,
        title=title,
        summary="",
        created_at=created_at,
        processing_duration=processing_duration,
        notion_page_id=notion_page_id,
        notion_url=notion_url,
    )


def sample_tasks_with_notion() -> list[Task]:
    return [
        build_task(
            id="1",
            title="Has URL",
            notion_url="https://www.notion.so/examplepage",
            created_offset_minutes=5,
            processing_duration=10.0,
        ),
        build_task(
            id="2",
            title="Has Page Id",
            notion_page_id="1234-5678",
            created_offset_minutes=10,
            processing_duration=12.5,
        ),
        build_task(
            id="3",
            title="Missing Notion",
            notion_page_id=None,
            notion_url=None,
            created_offset_minutes=15,
            processing_duration=None,
        ),
        build_task(
            id="4",
            title="Invalid URL",
            notion_url="ftp://invalid-link",
            created_offset_minutes=20,
            processing_duration=5.0,
        ),
    ]


def sample_tasks_for_sorting() -> list[Task]:
    return [
        build_task(id="10", title="Newest", created_offset_minutes=1),
        build_task(id="11", title="Middle", created_offset_minutes=5),
        build_task(id="12", title="Oldest", created_offset_minutes=30),
    ]
