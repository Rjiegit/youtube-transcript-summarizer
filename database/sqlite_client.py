import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from database.database_interface import BaseDB, ProcessingLockInfo
from database.task import Task
from database.task_adapter import SQLiteTaskAdapter


class SQLiteDB(BaseDB):
    """SQLite database connector."""

    def __init__(self, db_path: str = "data/tasks.db"):
        """Initializes the SQLite database."""
        self.db_path = db_path
        self.adapter = SQLiteTaskAdapter()
        self._create_table()

    def _get_connection(self) -> sqlite3.Connection:
        """Gets a connection to the SQLite database."""
        return sqlite3.connect(self.db_path)

    def _create_table(self) -> None:
        """Creates the tasks table if it doesn't exist and ensures required columns."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                status TEXT NOT NULL,
                title TEXT,
                summary TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processing_duration REAL,
                retry_of_task_id INTEGER,
                retry_reason TEXT,
                locked_at TIMESTAMP,
                worker_id TEXT,
                notion_page_id TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS processing_lock (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                worker_id TEXT,
                locked_at TIMESTAMP
            )
            """
        )

        # Ensure legacy databases get the new columns.
        cursor.execute("PRAGMA table_info(tasks)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        if "retry_of_task_id" not in existing_columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN retry_of_task_id INTEGER")
        if "retry_reason" not in existing_columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN retry_reason TEXT")
        if "locked_at" not in existing_columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN locked_at TIMESTAMP")
        if "worker_id" not in existing_columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN worker_id TEXT")
        if "notion_page_id" not in existing_columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN notion_page_id TEXT")

        conn.commit()
        conn.close()

    def add_task(self, url: str, status: str = "Pending") -> Task:
        """Adds a new task to the database and returns the stored record."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (url, status, title) VALUES (?, ?, ?)",
                (url, status, url),
            )
            new_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

        task = self.get_task_by_id(str(new_id))
        if task is None:  # pragma: no cover - defensive guard
            raise RuntimeError("Failed to load newly created task")
        return task

    def get_pending_tasks(self) -> list[Task]:
        """Gets all tasks with a 'Pending' status."""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE status = 'Pending'")
        tasks = [self.adapter.to_task(dict(row)) for row in cursor.fetchall()]
        conn.close()
        return tasks

    def get_all_tasks(self) -> list[Task]:
        """Gets all tasks from the database."""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks")
        tasks = [self.adapter.to_task(dict(row)) for row in cursor.fetchall()]
        conn.close()
        return tasks

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Gets a single task by its ID from the SQLite database."""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        return self.adapter.to_task(dict(row)) if row else None

    def acquire_next_task(
        self,
        worker_id: str,
        lock_timeout_seconds: int = 300,
    ) -> Optional[Task]:
        """Atomically select the next executable task and mark it as processing."""
        conn = self._get_connection()
        conn.isolation_level = None  # Explicit transaction control.
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 3000")
        cursor = conn.cursor()
        now = datetime.utcnow()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        stale_cutoff = (now - timedelta(seconds=lock_timeout_seconds)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        try:
            cursor.execute("BEGIN IMMEDIATE")
            candidate = cursor.execute(
                """
                SELECT id
                FROM tasks
                WHERE status = 'Pending'
                   OR (
                        status = 'Processing'
                        AND (
                            locked_at IS NULL
                            OR locked_at <= ?
                        )
                   )
                ORDER BY created_at ASC, id ASC
                LIMIT 1
                """,
                (stale_cutoff,),
            ).fetchone()

            if candidate is None:
                cursor.execute("COMMIT")
                return None

            task_id = candidate["id"]
            cursor.execute(
                """
                UPDATE tasks
                SET status = 'Processing',
                    worker_id = ?,
                    locked_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (worker_id, now_str, now_str, task_id),
            )

            if cursor.rowcount != 1:
                cursor.execute("ROLLBACK")
                return None

            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            cursor.execute("COMMIT")
            return self.adapter.to_task(dict(row)) if row else None
        except sqlite3.OperationalError:
            cursor.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def acquire_processing_lock(
        self,
        worker_id: str,
        lock_timeout_seconds: int = 300,
    ) -> bool:
        """Acquire a global processing lock to avoid concurrent workers."""
        conn = self._get_connection()
        conn.isolation_level = None
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 3000")
        cursor = conn.cursor()
        now = datetime.utcnow()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        stale_cutoff = now - timedelta(seconds=lock_timeout_seconds)

        try:
            cursor.execute("BEGIN IMMEDIATE")
            row = cursor.execute(
                "SELECT worker_id, locked_at FROM processing_lock WHERE id = 1"
            ).fetchone()

            if row and row["locked_at"]:
                try:
                    locked_at = datetime.fromisoformat(row["locked_at"])
                except ValueError:
                    locked_at = now
                if locked_at > stale_cutoff and row["worker_id"] != worker_id:
                    cursor.execute("ROLLBACK")
                    return False

            if row:
                cursor.execute(
                    """
                    UPDATE processing_lock
                    SET worker_id = ?, locked_at = ?
                    WHERE id = 1
                    """,
                    (worker_id, now_str),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO processing_lock (id, worker_id, locked_at)
                    VALUES (1, ?, ?)
                    """,
                    (worker_id, now_str),
                )

            cursor.execute("COMMIT")
            return True
        except sqlite3.OperationalError:
            cursor.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def refresh_processing_lock(self, worker_id: str) -> None:
        """Refresh the processing lock if the worker still owns it."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            UPDATE processing_lock
            SET locked_at = ?
            WHERE id = 1 AND worker_id = ?
            """,
            (now_str, worker_id),
        )
        conn.commit()
        conn.close()

    def release_processing_lock(self, worker_id: str) -> None:
        """Release the processing lock if held by the worker."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE processing_lock
            SET worker_id = NULL,
                locked_at = NULL
            WHERE id = 1 AND worker_id = ?
            """,
            (worker_id,),
        )
        conn.commit()
        conn.close()

    def read_processing_lock(self) -> ProcessingLockInfo:
        """Read the global processing lock metadata."""
        conn = self._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            row = cursor.execute(
                "SELECT worker_id, locked_at FROM processing_lock WHERE id = 1"
            ).fetchone()
        finally:
            conn.close()

        if not row or not row["worker_id"] or not row["locked_at"]:
            return ProcessingLockInfo(worker_id=None, locked_at=None)

        locked_at_raw = row["locked_at"]
        try:
            locked_at = datetime.fromisoformat(locked_at_raw)
        except ValueError:
            locked_at = datetime.utcnow()

        return ProcessingLockInfo(worker_id=row["worker_id"], locked_at=locked_at)

    def clear_processing_lock(self) -> None:
        """Unconditionally clear the global processing lock."""
        conn = self._get_connection()
        conn.isolation_level = None
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE")
            cursor.execute(
                """
                UPDATE processing_lock
                SET worker_id = NULL,
                    locked_at = NULL
                WHERE id = 1
                """
            )
            cursor.execute("COMMIT")
        except sqlite3.OperationalError:
            cursor.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def update_task_status(
        self,
        task_id: str,
        status: str,
        title: str = None,
        summary: str = None,
        error_message: str = None,
        processing_duration: float = None,
        notion_page_id: Optional[str] = None,
    ) -> None:
        """Updates the status and other fields of a task."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.now()

        set_clauses = ["status = ?", "updated_at = ?"]
        params: list[object] = [status, now]

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
        if notion_page_id is not None:
            set_clauses.append("notion_page_id = ?")
            params.append(notion_page_id)

        if status != "Processing":
            set_clauses.append("locked_at = NULL")
            set_clauses.append("worker_id = NULL")

        params.append(task_id)

        cursor.execute(
            f"""
            UPDATE tasks
            SET {', '.join(set_clauses)}
            WHERE id = ?
            """,
            tuple(params),
        )
        conn.commit()
        conn.close()

    def create_retry_task(
        self, source_task: Task, retry_reason: Optional[str] = None
    ) -> Task:
        """Creates a new pending task cloned from a failed task."""
        reason = retry_reason or source_task.error_message or "Manual retry"
        try:
            parent_id = int(source_task.id)
        except (TypeError, ValueError):
            parent_id = None

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (url, status, title, retry_of_task_id, retry_reason)
            VALUES (?, 'Pending', ?, ?, ?)
            """,
            (source_task.url, source_task.title or source_task.url, parent_id, reason),
        )
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        # Fresh read to return the full task representation.
        task = self.get_task_by_id(str(new_id))
        if task is None:  # pragma: no cover - defensive guard
            raise RuntimeError("Failed to load newly created retry task")
        return task
