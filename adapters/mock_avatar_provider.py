"""Deterministic mock provider for talking-avatar video generation."""

from __future__ import annotations

from common.errors import ExternalServiceError
from ports.outbound.avatar_provider import AvatarProviderPort
from services.avatar_generation.models import AvatarGeneratedVideo, AvatarJob


class MockAvatarProviderAdapter(AvatarProviderPort):
    """Mock provider with deterministic success and failure controls."""

    def __init__(self) -> None:
        self._should_fail = False
        self._failure_message = "Mock avatar provider failed."

    def configure_success(self) -> None:
        """Set the provider to return a deterministic successful result."""

        self._should_fail = False
        self._failure_message = "Mock avatar provider failed."

    def configure_failure(self, message: str = "Mock avatar provider failed.") -> None:
        """Set the provider to fail with a deterministic error message."""

        self._should_fail = True
        self._failure_message = message

    def generate_video(self, job: AvatarJob) -> AvatarGeneratedVideo:
        """Return deterministic bytes or raise a deterministic failure."""

        del job
        if self._should_fail:
            raise ExternalServiceError(
                self._failure_message,
                code="MOCK_PROVIDER_FAILURE",
            )
        return AvatarGeneratedVideo(
            content=b"mock-avatar-video",
            file_extension="mp4",
        )
