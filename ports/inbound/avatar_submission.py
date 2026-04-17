"""Inbound port for avatar job submission."""

from __future__ import annotations

from typing import Protocol

from services.avatar_generation.models import AvatarJob, AvatarSubmissionInput


class AvatarSubmissionPort(Protocol):
    """Creates a new avatar job from a validated submission request."""

    def create_avatar_job(self, submission: AvatarSubmissionInput) -> AvatarJob:
        """Validate the submission and persist a new pending avatar job."""
