import sqlite3
from datetime import datetime
from database.database_interface import BaseDB
from typing import List
from database.task import Task
from database.task_adapter import SQLiteTaskAdapter

class SQLiteDB(BaseDB):
    """SQLite database connector."""

    def __init__(self, db_path="data/tasks.db"):
        """Initializes the SQLite database."""
        self.db_path = db_path
        self.adapter = SQLiteTaskAdapter()
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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processing_duration REAL
            )
        """)
        conn.commit()
        conn.close()

    def add_task(self, url: str, status: str = "Pending") -> None:
        """Adds a new task to the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tasks (url, status, title) VALUES (?, ?, ?)", (url, status, url))
        conn.commit()
        conn.close()

    def get_pending_tasks(self) -> List[Task]:
        """Gets all tasks with a 'Pending' status."""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE status = 'Pending'")
        tasks = [self.adapter.to_task(dict(row)) for row in cursor.fetchall()]
        conn.close()
        return tasks

    def get_all_tasks(self) -> List[Task]:
        """Gets all tasks from the database."""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks")
        tasks = [self.adapter.to_task(dict(row)) for row in cursor.fetchall()]
        conn.close()
        return tasks

    def get_task_by_id(self, task_id: str) -> Task:
        """Gets a single task by its ID from the SQLite database."""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        return self.adapter.to_task(dict(row)) if row else None

    def update_task_status(self, task_id: str, status: str, title: str = None, summary: str = None, error_message: str = None, processing_duration: float = None) -> None:
        """Updates the status and other fields of a task."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now()
        
        set_clauses = ["status = ?", "updated_at = ?"]
        params = [status, now]

        if title is not None:
            set_clauses.append("title = ?")
            params.append(title)
        if summary is not None:
            set_clauses.append("summary = ?")
            params.append(summary)
        if error_message is not None:
            set_clauses.append("error_message = ?")
            params.append(error_message)
        if processing_duration is not None:
            set_clauses.append("processing_duration = ?")
            params.append(processing_duration)

        params.append(task_id) # Add task_id to the end

        cursor.execute(f"""
            UPDATE tasks
            SET {", ".join(set_clauses)}
            WHERE id = ?
        """, tuple(params))
        conn.commit()
        conn.close()
