"""API-layer models and response envelopes."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, Field


class AvatarJobPayload(Protocol):
    """Shape required to render an avatar job response payload."""

    job_id: str
    status: object
    voice: str
    script: str
    image_path: str


class ErrorInfo(BaseModel):
    """Standard API error payload."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ApiResponse(BaseModel):
    """Standard API envelope."""

    data: Any | None = None
    error: ErrorInfo | None = None


class AvatarJobResponse(BaseModel):
    """Submission response payload for a newly created avatar job."""

    job_id: str
    status: str
    voice: str
    script: str
    image_path: str

    @classmethod
    def from_domain(cls, job: AvatarJobPayload) -> "AvatarJobResponse":
        return cls(
            job_id=job.job_id,
            status=str(getattr(job.status, "value", job.status)),
            voice=job.voice,
            script=job.script,
            image_path=job.image_path,
        )


class AvatarSubmissionForm(BaseModel):
    """Typed representation of the multipart form fields."""

    script: str = ""
    voice: str | None = None
