"""Domain models for the talking avatar feature."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class AvatarJobStatus(StrEnum):
    """Allowed avatar job lifecycle states."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass(frozen=True)
class AvatarSubmissionInput:
    """User-provided data required to create a new avatar job."""

    original_filename: str | None
    declared_content_type: str | None
    image_bytes: bytes | None
    script: str | None
    selected_voice: str | None = None


@dataclass(frozen=True)
class AvatarValidationPolicy:
    """Centralized business-rule configuration for submissions."""

    default_voice: str
    max_script_length: int
    max_image_size_bytes: int
    supported_extensions: tuple[str, ...] = ("jpg", "jpeg", "png")


@dataclass(frozen=True)
class AvatarJob:
    """Persisted avatar job aggregate."""

    job_id: str
    script: str
    voice: str
    status: AvatarJobStatus
    image_path: str
    created_at: datetime
    updated_at: datetime
    generated_video_path: str | None = None
    provider_error_message: str | None = None
