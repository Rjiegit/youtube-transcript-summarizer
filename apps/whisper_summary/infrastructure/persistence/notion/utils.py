from __future__ import annotations

from typing import List

NOTION_RICH_TEXT_LIMIT = 1800


def chunk_text(content: str | None, limit: int = NOTION_RICH_TEXT_LIMIT) -> List[str]:
    """Split content into chunks acceptable by Notion rich_text blocks."""
    if not content:
        return []

    return [content[i : i + limit] for i in range(0, len(content), limit)]


def build_rich_text_array(content: str | None) -> List[dict]:
    """Convert text into the structure expected by Notion rich_text properties."""
    chunks = chunk_text(content)
    return [{"type": "text", "text": {"content": chunk}} for chunk in chunks]
