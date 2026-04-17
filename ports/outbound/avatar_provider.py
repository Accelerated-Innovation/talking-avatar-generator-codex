"""Outbound port for avatar video generation providers."""

from __future__ import annotations

from typing import Protocol

from services.avatar_generation.models import AvatarGeneratedVideo, AvatarJob


class AvatarProviderPort(Protocol):
    """Generates a talking-avatar video for a processing job."""

    def generate_video(self, job: AvatarJob) -> AvatarGeneratedVideo:
        """Generate a video payload for the provided job."""
