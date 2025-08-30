from abc import ABC, abstractmethod
from typing import Dict, Any
from db.task import Task

class TaskAdapter(ABC):
    @abstractmethod
    def to_task(self, data: Dict[str, Any]) -> Task:
        pass

class NotionTaskAdapter(TaskAdapter):
    def to_task(self, data: Dict[str, Any]) -> Task:
        summary_list = data['properties']['Summary']['rich_text']
        summary = summary_list[0]['text']['content'] if summary_list else ''
        return Task(
            id=data['id'],
            url=data['properties']['URL']['url'],
            status=data['properties']['Status']['select']['name'],
            summary=summary
        )

class SQLiteTaskAdapter(TaskAdapter):
    def to_task(self, data: Dict[str, Any]) -> Task:
        return Task(
            id=data['id'],
            url=data['url'],
            status=data['status'],
            summary=data['summary'] or ""
        )
