"""Outbound port for avatar job persistence."""

from __future__ import annotations

from typing import Protocol

from services.avatar_generation.models import AvatarJob


class AvatarJobRepositoryPort(Protocol):
    """Persists and loads avatar jobs."""

    def create(self, job: AvatarJob) -> AvatarJob:
        """Create a new avatar job."""

    def get_by_id(self, job_id: str) -> AvatarJob | None:
        """Return the matching job when it exists."""

    def update(self, job: AvatarJob) -> AvatarJob:
        """Persist updates to an existing avatar job."""
