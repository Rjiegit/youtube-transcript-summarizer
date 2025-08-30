import sqlite3
from datetime import datetime
from database_interface import BaseDB
from typing import List, Dict, Any

class SQLiteDB(BaseDB):
    """SQLite database connector."""

    def __init__(self, db_path="data/tasks.db"):
        """Initializes the SQLite database."""
        self.db_path = db_path
        self._create_table()

    def _get_connection(self):
        """Gets a connection to the SQLite database."""
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        """Creates the tasks table if it doesn't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                status TEXT NOT NULL,
                title TEXT,
                summary TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def add_task(self, url: str, status: str = "Pending") -> None:
        """Adds a new task to the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (url, status) VALUES (?, ?)", (url, status))
        conn.commit()
        conn.close()

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Gets all tasks with a 'Pending' status."""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE status = 'Pending'")
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tasks

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Gets all tasks from the database."""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks")
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tasks

    def update_task_status(self, task_id: str, status: str, summary: str = None, error_message: str = None) -> None:
        """Updates the status of a task."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now()
        cursor.execute("""
            UPDATE tasks
            SET status = ?, summary = ?, error_message = ?, updated_at = ?
            WHERE id = ?
        """, (status, summary, error_message, now, task_id))
        conn.commit()
        conn.close()
