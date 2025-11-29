from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Task:
    id: str
    url: str
    status: str
    title: str = ""
    summary: str = ""
    created_at: Optional[datetime] = None
    processing_duration: Optional[float] = None
    error_message: str = ""
    retry_of_task_id: Optional[str] = None
    retry_reason: str = ""
    locked_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    notion_page_id: Optional[str] = None
    notion_url: Optional[str] = None
