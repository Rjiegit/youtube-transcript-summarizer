from __future__ import annotations

from typing import Any, Dict


def build_notion_url(
    *,
    notion_base_url: str | None,
    notion_page_id: str | None,
    existing_url: str | None = None,
) -> str | None:
    """Construct a Notion URL from an existing link or base URL + page id."""
    if existing_url:
        return existing_url.strip()
    if not notion_base_url or not notion_page_id:
        return None
    cleaned_id = notion_page_id.replace("-", "")
    return f"{notion_base_url.rstrip('/')}/{cleaned_id}"


def get_notion_display(task: Any, notion_base_url: str | None) -> Dict[str, str]:
    """Decide how to display Notion URL for a task."""
    url = build_notion_url(
        notion_base_url=notion_base_url,
        notion_page_id=getattr(task, "notion_page_id", None),
        existing_url=getattr(task, "notion_url", None),
    )
    if url:
        if url.startswith("http://") or url.startswith("https://"):
            return {"status": "link", "url": url}
        return {"status": "invalid", "message": "Notion URL 格式錯誤"}
    placeholder = "Notion 未設定" if not notion_base_url else "尚未同步到 Notion"
    return {"status": "missing", "message": placeholder}
