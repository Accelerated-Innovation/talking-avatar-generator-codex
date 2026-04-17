"""Inbound port for avatar job lifecycle processing."""

from __future__ import annotations

from typing import Protocol

from services.avatar_generation.models import AvatarJob


class AvatarProcessingPort(Protocol):
    """Advances avatar jobs through processing lifecycle states."""

    def start_processing(self, job_id: str) -> AvatarJob:
        """Move a pending avatar job into processing."""

    def complete_processing(self, job_id: str) -> AvatarJob:
        """Finish processing a job as complete or failed."""
