from dataclasses import dataclass
from datetime import datetime

@dataclass
class Task:
    id: str
    url: str
    status: str
    title: str = ""
    summary: str = ""
    created_at: datetime = None
