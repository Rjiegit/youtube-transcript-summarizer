from __future__ import annotations

import os
from pathlib import Path

API_BASE_URL = os.environ.get("TASK_API_BASE_URL", "http://localhost:8080")
NOTION_BASE_URL = os.environ.get("NOTION_URL")
RECENT_TASK_HISTORY_KEY = "recent_task_history"
RECENT_TASK_HISTORY_TTL_DAYS = 30
RECENT_TASK_HISTORY_STORE_PATH = Path("data/ui_recent_history.json")
