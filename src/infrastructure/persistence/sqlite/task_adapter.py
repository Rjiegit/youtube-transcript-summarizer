from abc import ABC, abstractmethod
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.domain.tasks.models import Task


def _extract_rich_text_content(items: Optional[List[Dict[str, Any]]]) -> str:
    if not items:
        return ""
    contents = []
    for item in items:
        text = item.get("text", {})
        contents.append(text.get("content", ""))
    return "".join(contents)


def _build_notion_url(page_id: Optional[str]) -> Optional[str]:
    """Construct a Notion page URL using NOTION_URL and page id if available."""
    base = os.environ.get("NOTION_URL")
    if not base or not page_id:
        return None
    cleaned_id = str(page_id).replace("-", "")
    normalized_base = base.rstrip("/")
    return f"{normalized_base}/{cleaned_id}"


class TaskAdapter(ABC):
    @abstractmethod
    def to_task(self, data: Dict[str, Any]) -> Task:
        raise NotImplementedError


class NotionTaskAdapter(TaskAdapter):
    def to_task(self, data: Dict[str, Any]) -> Task:
        properties = data.get("properties", {})

        summary = _extract_rich_text_content(
            properties.get("Summary", {}).get("rich_text")
        )
        title = _extract_rich_text_content(properties.get("Name", {}).get("title"))
        error_message = _extract_rich_text_content(
            properties.get("Error Message", {}).get("rich_text")
        )
        retry_reason = _extract_rich_text_content(
            properties.get("Retry Reason", {}).get("rich_text")
        )
        retry_relations = properties.get("Retry Of", {}).get("relation", [])
        retry_of_task_id = retry_relations[0]["id"] if retry_relations else None
        processing_duration = properties.get("Processing Duration", {}).get("number")

        notion_id = data.get("id")
        notion_page_id = str(notion_id) if notion_id is not None else None
        notion_url = _build_notion_url(notion_page_id)
        return Task(
            id=str(notion_id) if notion_id is not None else "",
            url=properties.get("URL", {}).get("url", ""),
            status=(properties.get("Status", {}).get("select") or {}).get("name", ""),
            title=title,
            summary=summary,
            created_at=datetime.fromisoformat(data["created_time"]),
            processing_duration=processing_duration,
            error_message=error_message,
            retry_of_task_id=retry_of_task_id,
            retry_reason=retry_reason,
            locked_at=None,
            worker_id=None,
            notion_page_id=notion_page_id,
            notion_url=notion_url,
        )


class SQLiteTaskAdapter(TaskAdapter):
    def to_task(self, data: Dict[str, Any]) -> Task:
        created_at_value = data.get("created_at")
        created_at = (
            datetime.fromisoformat(created_at_value)
            if created_at_value is not None
            else None
        )
        retry_of_id = data.get("retry_of_task_id")
        if retry_of_id is not None:
            retry_of_id = str(retry_of_id)

        raw_id = data.get("id")
        task_id = str(raw_id) if raw_id is not None else ""
        locked_at_value = data.get("locked_at")
        locked_at = (
            datetime.fromisoformat(locked_at_value)
            if locked_at_value is not None
            else None
        )
        notion_page = data.get("notion_page_id")
        notion_page_id = str(notion_page) if notion_page is not None else None
        notion_url = _build_notion_url(notion_page_id)
        return Task(
            id=task_id,
            url=data.get("url", ""),
            status=data.get("status", ""),
            title=(data.get("title") or ""),
            summary=(data.get("summary") or ""),
            created_at=created_at,
            processing_duration=data.get("processing_duration"),
            error_message=(data.get("error_message") or ""),
            retry_of_task_id=retry_of_id,
            retry_reason=(data.get("retry_reason") or ""),
            locked_at=locked_at,
            worker_id=data.get("worker_id"),
            notion_page_id=notion_page_id,
            notion_url=notion_url,
        )
