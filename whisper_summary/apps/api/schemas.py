"""Pydantic request and response schemas for the Task API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from whisper_summary.core.utils.url import is_valid_youtube_channel_id

SUPPORTED_DB_TYPES = {"sqlite", "notion"}


def normalize_db_type(value: str) -> str:
    normalized = (value or "").lower()
    if normalized not in SUPPORTED_DB_TYPES:
        raise ValueError("db_type must be either 'sqlite' or 'notion'.")
    return normalized


class TaskCreateRequest(BaseModel):
    """Incoming payload for creating a new task."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    url: str = Field(..., description="YouTube URL to add to the processing queue.")
    db_type: str = Field(
        default="sqlite",
        description="Database backend to persist the task (sqlite|notion).",
    )
    source_type: str = Field(
        default="manual",
        description="Origin of the task creation request (manual|rss).",
    )
    source_channel_id: str | None = Field(
        default=None,
        description="Optional source channel identifier when the task was created from RSS.",
    )
    completed_task_policy: str = Field(
        default="cache_ttl",
        description="Completed-task dedup policy (cache_ttl|block_existing).",
    )

    @field_validator("url")
    @classmethod
    def validate_url_presence(cls, value: str) -> str:
        if not value:
            raise ValueError("URL is required.")
        return value

    @field_validator("db_type")
    @classmethod
    def normalize_db_type(cls, value: str) -> str:
        normalized = (value or "").lower()
        if normalized not in SUPPORTED_DB_TYPES:
            raise ValueError("db_type must be either 'sqlite' or 'notion'.")
        return normalized

    @field_validator("source_type")
    @classmethod
    def normalize_source_type(cls, value: str) -> str:
        normalized = (value or "").lower()
        if normalized not in {"manual", "rss"}:
            raise ValueError("source_type must be either 'manual' or 'rss'.")
        return normalized

    @field_validator("completed_task_policy")
    @classmethod
    def normalize_completed_task_policy(cls, value: str) -> str:
        normalized = (value or "").lower()
        if normalized not in {"cache_ttl", "block_existing"}:
            raise ValueError(
                "completed_task_policy must be either 'cache_ttl' or 'block_existing'."
            )
        return normalized


class TaskCreateResponse(BaseModel):
    """Standard response after creating a task."""

    task_id: str = Field(..., description="Identifier of the queued task.")
    status: str = Field(..., description="Current status of the task.")
    db_type: str = Field(..., description="Database backend used to persist the task.")
    message: str = Field(..., description="Human readable status message.")
    processing_started: bool = Field(
        default=False,
        description="Indicates whether a background worker was scheduled.",
    )
    processing_worker_id: str | None = Field(
        default=None,
        description="Worker identifier if background processing was scheduled.",
    )
    cached: bool = Field(
        default=False,
        description="True when the response was served from a recent completed task.",
    )


class TaskRetryRequest(BaseModel):
    """Incoming payload for retrying a failed task."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    db_type: str = Field(
        default="sqlite",
        description="Database backend to persist the retry task (sqlite|notion).",
    )
    retry_reason: str | None = Field(
        default=None,
        description="Optional reason for retrying the task.",
    )

    @field_validator("db_type")
    @classmethod
    def normalize_db_type(cls, value: str) -> str:
        normalized = (value or "").lower()
        if normalized not in SUPPORTED_DB_TYPES:
            raise ValueError("db_type must be either 'sqlite' or 'notion'.")
        return normalized


class TaskRetryResponse(BaseModel):
    """Standard response after creating a retry task."""

    task_id: str = Field(..., description="Identifier of the newly created retry task.")
    source_task_id: str = Field(..., description="Identifier of the failed task being retried.")
    status: str = Field(..., description="Current status of the retry task.")
    db_type: str = Field(..., description="Database backend used to persist the retry task.")
    message: str = Field(..., description="Human readable status message.")


class RSSSubscriptionCreateRequest(BaseModel):
    """Incoming payload for creating an RSS channel subscription."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    channel_id: str = Field(..., description="YouTube channel id.")
    feed_url: str | None = Field(
        default=None,
        description="Optional canonical YouTube feed URL for the channel.",
    )
    title: str | None = Field(
        default="",
        description="Optional display title for the subscription.",
    )
    enabled: bool = Field(
        default=True,
        description="Whether the subscription should be enabled immediately.",
    )

    @field_validator("channel_id")
    @classmethod
    def validate_channel_id(cls, value: str) -> str:
        if not is_valid_youtube_channel_id(value):
            raise ValueError("channel_id must be a valid YouTube channel id.")
        return value


class RSSSubscriptionCreateResponse(BaseModel):
    """Response payload after creating an RSS subscription."""

    subscription_id: str = Field(..., description="Identifier of the subscription.")
    channel_id: str = Field(..., description="YouTube channel id.")
    feed_url: str = Field(..., description="Canonical YouTube feed URL.")
    title: str = Field(..., description="Display title for the subscription.")
    enabled: bool = Field(..., description="Whether the subscription is enabled.")
    message: str = Field(..., description="Human readable status message.")


class ProcessingJobCreateRequest(BaseModel):
    """Incoming payload for triggering the processing worker."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    db_type: str = Field(
        default="sqlite",
        description="Database backend to drain tasks from (sqlite|notion).",
    )
    worker_id: str | None = Field(
        default=None,
        description="Optional human-readable worker identifier.",
    )

    @field_validator("db_type")
    @classmethod
    def normalize_db_type(cls, value: str) -> str:
        normalized = (value or "").lower()
        if normalized not in SUPPORTED_DB_TYPES:
            raise ValueError("db_type must be either 'sqlite' or 'notion'.")
        return normalized


class ProcessingJobCreateResponse(BaseModel):
    """Response payload after scheduling a processing job."""

    worker_id: str = Field(..., description="Identifier assigned to the worker run.")
    db_type: str = Field(..., description="Database backend being processed.")
    accepted: bool = Field(..., description="Indicates whether the run was scheduled.")
    message: str = Field(..., description="Human readable status message.")


class ProcessingLockSnapshot(BaseModel):
    """Representation of the processing lock state for inspection."""

    model_config = ConfigDict(extra="forbid")

    worker_id: str | None = Field(
        default=None,
        description="Identifier of the worker holding the lock.",
    )
    locked_at: datetime | None = Field(
        default=None,
        description="UTC timestamp of when the lock was last refreshed.",
    )
    age_seconds: float | None = Field(
        default=None,
        description="Seconds since the lock was last refreshed.",
    )
    stale: bool = Field(
        default=False,
        description="Indicates whether the lock has exceeded the timeout threshold.",
    )


class ProcessingLockStatusResponse(BaseModel):
    """Response payload for GET /processing-lock."""

    model_config = ConfigDict(extra="forbid")

    db_type: str = Field(..., description="Database backend being inspected.")
    snapshot: ProcessingLockSnapshot = Field(
        ...,
        description="Snapshot of the current processing lock.",
    )


class ProcessingLockReleaseRequest(BaseModel):
    """Incoming payload when attempting to release the processing lock."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    db_type: str = Field(
        default="sqlite",
        description="Database backend whose lock is being inspected (sqlite|notion).",
    )
    expected_worker_id: str | None = Field(
        default=None,
        description="Worker ID that must match the current lock holder (unless force=true).",
    )
    force: bool = Field(
        default=False,
        description="Whether to forcibly clear the lock even if the expected worker does not match.",
    )
    force_threshold_seconds: int | None = Field(
        default=None,
        description="Minimum age (in seconds) the lock must reach before a forced clear is allowed.",
    )
    reason: str | None = Field(
        default=None,
        description="Human-readable note describing why the lock is being released.",
    )
    dry_run: bool = Field(
        default=False,
        description="If true, the API only reports the current lock state without modifying it.",
    )

    @field_validator("db_type")
    @classmethod
    def _normalize_db_type(cls, value: str) -> str:
        return normalize_db_type(value)

    @field_validator("force_threshold_seconds")
    @classmethod
    def _validate_threshold(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value < 0:
            raise ValueError("force_threshold_seconds must be greater than or equal to 0.")
        return value


class ProcessingLockReleaseResponse(BaseModel):
    """Response payload after attempting to release the lock."""

    model_config = ConfigDict(extra="forbid")

    db_type: str = Field(..., description="Database backend that was inspected.")
    released: bool = Field(
        ...,
        description="True if the lock was cleared; false if it remained untouched.",
    )
    reason: str | None = Field(
        default=None,
        description="Optional explanation for why the lock was or was not released.",
    )
    before: ProcessingLockSnapshot = Field(
        ...,
        description="Lock snapshot observed before any action.",
    )
    after: ProcessingLockSnapshot = Field(
        ...,
        description="Lock snapshot after taking the requested action.",
    )



