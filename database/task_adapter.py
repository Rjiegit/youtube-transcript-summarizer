from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from database.task import Task


def _extract_rich_text_content(items: Optional[List[Dict[str, Any]]]) -> str:
    if not items:
        return ""
    contents = []
    for item in items:
        text = item.get("text", {})
        contents.append(text.get("content", ""))
    return "".join(contents)


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
        )
