"""Unit tests for avatar submission and validation logic."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime

import pytest

from common.errors import ValidationError
from ports.inbound.avatar_submission import AvatarSubmissionInput
from ports.outbound.clock import Clock
from ports.outbound.observability import ObservabilityPort
from services.avatar_generation.models import (
    AvatarGeneratedVideo,
    AvatarJob,
    AvatarJobStatus,
    AvatarValidationPolicy,
)
from services.avatar_generation.service import AvatarGenerationService


class FakeRepository:
    def __init__(self) -> None:
        self.created_jobs: list[AvatarJob] = []

    def create(self, job: AvatarJob) -> AvatarJob:
        self.created_jobs.append(job)
        return job

    def get_by_id(self, job_id: str) -> AvatarJob | None:
        for job in self.created_jobs:
            if job.job_id == job_id:
                return job
        return None

    def update(self, job: AvatarJob) -> AvatarJob:
        return job


class FakeStorage:
    def __init__(self) -> None:
        self.saved_assets: list[tuple[str, bytes, str]] = []

    def save_asset(self, filename: str, content: bytes, *, category: str) -> str:
        self.saved_assets.append((filename, content, category))
        return f"{category}/{filename}"


class FakeObservability(ObservabilityPort):
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def record_event(self, event: str, *, level: str = "info", **attributes):
        self.events.append({"event": event, "level": level, **attributes})

    @contextmanager
    def start_span(self, name: str, *, attributes=None):
        yield None

    def increment_counter(self, name: str, value: int = 1, *, tags=None) -> None:
        return None


class FakeAvatarProvider:
    def generate_video(self, job: AvatarJob) -> AvatarGeneratedVideo:
        del job
        return AvatarGeneratedVideo(content=b"mock-video", file_extension="mp4")


class FixedClock(Clock):
    def __init__(self, timestamp: datetime) -> None:
        self._timestamp = timestamp

    def now(self) -> datetime:
        return self._timestamp


@pytest.fixture()
def validation_policy() -> AvatarValidationPolicy:
    return AvatarValidationPolicy(
        default_voice="Default Voice",
        max_script_length=300,
        max_image_size_bytes=5 * 1024 * 1024,
    )


def create_service(validation_policy: AvatarValidationPolicy):
    repository = FakeRepository()
    storage = FakeStorage()
    provider = FakeAvatarProvider()
    observability = FakeObservability()
    clock = FixedClock(datetime(2026, 4, 16, tzinfo=UTC))
    service = AvatarGenerationService(
        repository=repository,
        asset_storage=storage,
        provider=provider,
        observability=observability,
        clock=clock,
        validation_policy=validation_policy,
    )
    return service, repository, storage, observability


def test_create_avatar_job_persists_pending_job_with_generated_filename(
    validation_policy: AvatarValidationPolicy,
) -> None:
    service, repository, storage, observability = create_service(validation_policy)

    job = service.create_avatar_job(
        AvatarSubmissionInput(
            original_filename="portrait.png",
            declared_content_type="image/png",
            image_bytes=(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
                b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
                b"\x00\x00\x0bIDATx\x9cc`\x00\x02\x00\x00\x05\x00\x01"
                b"\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
            ),
            script="Hello avatar",
            selected_voice=None,
        )
    )

    assert job.status is AvatarJobStatus.PENDING
    assert job.voice == "Default Voice"
    assert repository.created_jobs == [job]
    assert storage.saved_assets[0][2] == "portraits"
    assert storage.saved_assets[0][0] != "portrait.png"
    assert storage.saved_assets[0][0].endswith(".png")
    assert observability.events[0]["event"] == "avatar_job_created"


def test_create_avatar_job_rejects_missing_image_without_persisting_job(
    validation_policy: AvatarValidationPolicy,
) -> None:
    service, repository, _, _ = create_service(validation_policy)

    with pytest.raises(ValidationError, match="portrait image is required"):
        service.create_avatar_job(
            AvatarSubmissionInput(
                original_filename=None,
                declared_content_type=None,
                image_bytes=None,
                script="Hello avatar",
            )
        )

    assert repository.created_jobs == []


def test_create_avatar_job_rejects_unsupported_image_type(
    validation_policy: AvatarValidationPolicy,
) -> None:
    service, repository, _, _ = create_service(validation_policy)

    with pytest.raises(ValidationError, match="Unsupported image type"):
        service.create_avatar_job(
            AvatarSubmissionInput(
                original_filename="portrait.gif",
                declared_content_type="image/gif",
                image_bytes=b"GIF89a",
                script="Hello avatar",
            )
        )

    assert repository.created_jobs == []


def test_create_avatar_job_rejects_image_that_exceeds_max_size(
    validation_policy: AvatarValidationPolicy,
) -> None:
    service, repository, _, _ = create_service(validation_policy)

    with pytest.raises(ValidationError, match="5 MB or smaller"):
        service.create_avatar_job(
            AvatarSubmissionInput(
                original_filename="portrait.png",
                declared_content_type="image/png",
                image_bytes=b"a" * ((5 * 1024 * 1024) + 1),
                script="Hello avatar",
            )
        )

    assert repository.created_jobs == []


def test_create_avatar_job_rejects_missing_script(
    validation_policy: AvatarValidationPolicy,
) -> None:
    service, repository, _, _ = create_service(validation_policy)

    with pytest.raises(ValidationError, match="script is required"):
        service.create_avatar_job(
            AvatarSubmissionInput(
                original_filename="portrait.png",
                declared_content_type="image/png",
                image_bytes=(
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
                    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
                    b"\x00\x00\x0bIDATx\x9cc`\x00\x02\x00\x00\x05\x00\x01"
                    b"\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
                ),
                script="  ",
            )
        )

    assert repository.created_jobs == []


def test_create_avatar_job_rejects_script_longer_than_max_length(
    validation_policy: AvatarValidationPolicy,
) -> None:
    service, repository, _, _ = create_service(validation_policy)

    with pytest.raises(ValidationError, match="300 characters or fewer"):
        service.create_avatar_job(
            AvatarSubmissionInput(
                original_filename="portrait.png",
                declared_content_type="image/png",
                image_bytes=(
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
                    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00"
                    b"\x00\x00\x0bIDATx\x9cc`\x00\x02\x00\x00\x05\x00\x01"
                    b"\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
                ),
                script="x" * 301,
            )
        )

    assert repository.created_jobs == []


def test_create_avatar_job_rejects_unsupported_image_content(
    validation_policy: AvatarValidationPolicy,
) -> None:
    service, repository, _, _ = create_service(validation_policy)

    with pytest.raises(ValidationError, match="not a supported image"):
        service.create_avatar_job(
            AvatarSubmissionInput(
                original_filename="portrait.png",
                declared_content_type="image/png",
                image_bytes=b"not-a-real-image",
                script="Hello avatar",
            )
        )

    assert repository.created_jobs == []


def test_create_avatar_job_rejects_mismatched_declared_image_type(
    validation_policy: AvatarValidationPolicy,
) -> None:
    service, repository, _, _ = create_service(validation_policy)

    with pytest.raises(ValidationError, match="does not match the declared image type"):
        service.create_avatar_job(
            AvatarSubmissionInput(
                original_filename="portrait.png",
                declared_content_type="image/png",
                image_bytes=(
                    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01"
                    b"\x00\x01\x00\x00"
                ),
                script="Hello avatar",
            )
        )

    assert repository.created_jobs == []
