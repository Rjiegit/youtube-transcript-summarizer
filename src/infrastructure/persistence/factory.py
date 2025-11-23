from src.domain.interfaces.database import BaseDB
from src.infrastructure.persistence.sqlite.client import SQLiteDB


class DBFactory:
    @staticmethod
    def get_db(db_type: str) -> BaseDB:
        if db_type.lower() == "notion":
            try:
                from src.infrastructure.persistence.notion.client import NotionDB
            except ImportError as exc:  # pragma: no cover - optional dependency path
                raise RuntimeError(
                    "Notion client is not available. Install notion-client to use this option."
                ) from exc
            return NotionDB()
        if db_type.lower() == "sqlite":
            return SQLiteDB()
        raise ValueError(f"Unknown database type: {db_type}")
