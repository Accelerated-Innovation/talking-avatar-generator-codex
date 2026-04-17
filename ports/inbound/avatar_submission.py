"""Inbound port for avatar job submission."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from services.avatar_generation.models import AvatarJob


@dataclass(frozen=True)
class AvatarSubmissionInput:
    """User-provided data required to create a new avatar job."""

    original_filename: str | None
    declared_content_type: str | None
    image_bytes: bytes | None
    script: str | None
    selected_voice: str | None = None


class AvatarSubmissionPort(Protocol):
    """Creates a new avatar job from a validated submission request."""

    def create_avatar_job(self, submission: AvatarSubmissionInput) -> AvatarJob:
        """Validate the submission and persist a new pending avatar job."""
