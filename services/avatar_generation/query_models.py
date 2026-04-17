"""Query models for avatar job detail rendering."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AvatarJobDetailView:
    """Status-aware data required by the detail page."""

    job_id: str
    status: str
    script: str
    voice: str
    image_path: str
    generated_video_path: str | None
    provider_error_message: str | None
    show_generated_video: bool
