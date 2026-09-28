"""FastAPI application assembly for task management endpoints."""

from fastapi import FastAPI

from whisper_summary.apps.api.routers.processing import router as processing_router
from whisper_summary.apps.api.routers.rss import router as rss_router
from whisper_summary.apps.api.routers.tasks import router as tasks_router

app = FastAPI(
    title="Task API",
    version="1.0.0",
    description="HTTP endpoints for managing transcription tasks.",
)
app.include_router(tasks_router)
app.include_router(rss_router)
app.include_router(processing_router)
