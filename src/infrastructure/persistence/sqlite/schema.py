import sqlite3


def initialize_schema(conn: sqlite3.Connection) -> None:
    """Create application tables and upgrade legacy task columns."""
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
            notion_page_id TEXT,
            source_type TEXT DEFAULT 'manual',
            source_channel_id TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS recent_task_history (
            task_id TEXT PRIMARY KEY,
            viewed_at TIMESTAMP NOT NULL
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
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rss_channel_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL UNIQUE,
            feed_url TEXT NOT NULL,
            title TEXT,
            enabled INTEGER NOT NULL DEFAULT 1,
            last_processed_published_at TIMESTAMP,
            last_checked_at TIMESTAMP,
            last_status TEXT,
            last_error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_rss_channel_subscriptions_enabled
        ON rss_channel_subscriptions (enabled, channel_id)
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
    if "source_type" not in existing_columns:
        cursor.execute("ALTER TABLE tasks ADD COLUMN source_type TEXT DEFAULT 'manual'")
    if "source_channel_id" not in existing_columns:
        cursor.execute("ALTER TABLE tasks ADD COLUMN source_channel_id TEXT")

    conn.commit()


