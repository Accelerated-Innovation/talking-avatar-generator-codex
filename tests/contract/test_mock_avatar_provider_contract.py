"""Contract tests for the deterministic mock avatar provider adapter."""

from __future__ import annotations

import pytest

from adapters.mock_avatar_provider import MockAvatarProviderAdapter
from common.errors import ExternalServiceError
from services.avatar_generation.models import AvatarJob, AvatarJobStatus


def build_job() -> AvatarJob:
    from datetime import UTC, datetime

    timestamp = datetime(2026, 4, 16, tzinfo=UTC)
    return AvatarJob(
        job_id="job-123",
        script="Hello avatar",
        voice="Default Voice",
        status=AvatarJobStatus.PROCESSING,
        image_path="portraits/job-123.png",
        created_at=timestamp,
        updated_at=timestamp,
    )


def test_mock_avatar_provider_returns_deterministic_video_payload() -> None:
    provider = MockAvatarProviderAdapter()

    generated_video = provider.generate_video(build_job())

    assert generated_video.file_extension == "mp4"
    assert generated_video.content == b"mock-avatar-video"


def test_mock_avatar_provider_raises_external_service_error_when_configured_to_fail() -> None:
    provider = MockAvatarProviderAdapter()
    provider.configure_failure("Mock provider outage")

    with pytest.raises(ExternalServiceError, match="Mock provider outage"):
        provider.generate_video(build_job())
