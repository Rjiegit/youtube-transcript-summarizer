import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import os

from db import SQLiteDB

class TestSQLiteDB(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.db = SQLiteDB(db_path=self.db_path)

    def test_add_task(self):
        """Test adding a task to the database."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            url = "https://www.youtube.com/watch?v=test"
            self.db.add_task(url)

            mock_cursor.execute.assert_any_call("INSERT INTO tasks (url, status) VALUES (?, ?)", (url, "Pending"))
            mock_conn.commit.assert_called_once()
            mock_conn.close.assert_called_once()

    def test_get_pending_tasks(self):
        """Test getting pending tasks from the database."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.fetchall.return_value = [
                {'id': 1, 'url': 'test_url', 'status': 'Pending'}
            ]
            mock_conn.row_factory = sqlite3.Row


            tasks = self.db.get_pending_tasks()

            mock_cursor.execute.assert_called_with("SELECT * FROM tasks WHERE status = 'Pending'")
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0]['id'], 1)

    def test_update_task_status(self):
        """Test updating a task status in the database."""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            task_id = 1
            status = "Completed"
            summary = "This is a summary."
            self.db.update_task_status(task_id, status, summary=summary)

            mock_cursor.execute.assert_called_once()
            self.assertEqual(mock_cursor.execute.call_args[0][0].strip(), "UPDATE tasks\n            SET status = ?, summary = ?, error_message = ?, updated_at = ?\n            WHERE id = ?")
            self.assertEqual(mock_cursor.execute.call_args[0][1][0], status)
            self.assertEqual(mock_cursor.execute.call_args[0][1][1], summary)

if __name__ == '__main__':
    unittest.main()