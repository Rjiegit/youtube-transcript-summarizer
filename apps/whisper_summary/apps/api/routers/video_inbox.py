"""Authenticated local API for durable cloud inbox delivery."""
import os
import sqlite3

from fastapi import APIRouter, Header, HTTPException, status
from whisper_summary.apps.api.dependencies import get_database
from whisper_summary.apps.api.routers.processing import ensure_worker_token
from whisper_summary.apps.api.schemas import VideoInboxEnvelope
from whisper_summary.services.tasks.video_inbox import persist_message

router = APIRouter()


@router.post('/video-inbox/messages')
def receive_video_inbox_message(
    envelope: VideoInboxEnvelope,
    worker_token: str | None = Header(None, alias='X-Worker-Token'),
):
    ensure_worker_token(worker_token)
    try:
        db = get_database('sqlite')
        outcome = persist_message(db, envelope.model_dump(),
                                  cache_ttl_seconds=int(os.getenv('TASK_CACHE_TTL_SECONDS', '3600')))
    except sqlite3.Error as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail='Local task database unavailable.') from exc
    return {'outcome': outcome}
