from database.notion_client import NotionDB
from database.sqlite_client import SQLiteDB
from database.database_interface import BaseDB

class DBFactory:
    @staticmethod
    def get_db(db_type: str) -> BaseDB:
        if db_type.lower() == "notion":
            return NotionDB()
        elif db_type.lower() == "sqlite":
            return SQLiteDB()
        else:
            raise ValueError(f"Unknown database type: {db_type}")
