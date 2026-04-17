"""Inbound port for avatar job detail retrieval."""

from __future__ import annotations

from typing import Protocol

from services.avatar_generation.query_models import AvatarJobDetailView


class AvatarJobQueryPort(Protocol):
    """Retrieves shaped detail data for avatar job pages."""

    def get_avatar_job_detail(self, job_id: str) -> AvatarJobDetailView:
        """Return a shaped detail view for the requested job."""
