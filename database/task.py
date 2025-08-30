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
    created_at: datetime = None
    processing_duration: Optional[float] = None
