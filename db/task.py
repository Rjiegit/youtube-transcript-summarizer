from dataclasses import dataclass

@dataclass
class Task:
    id: str
    url: str
    status: str
    summary: str = ""
