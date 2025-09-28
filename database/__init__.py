from .database_interface import BaseDB
from .sqlite_client import SQLiteDB

try:  # pragma: no cover - optional dependency
    from .notion_client import NotionDB
except ImportError:  # pragma: no cover - optional dependency
    NotionDB = None

__all__ = ["BaseDB", "NotionDB", "SQLiteDB"]
