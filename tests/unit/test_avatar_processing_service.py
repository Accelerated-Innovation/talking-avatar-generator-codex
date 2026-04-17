"""Unit tests for avatar job processing lifecycle behavior."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime

import pytest

from common.errors import ExternalServiceError, NotFoundError
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
        self.jobs_by_id: dict[str, AvatarJob] = {}

    def create(self, job: AvatarJob) -> AvatarJob:
        self.jobs_by_id[job.job_id] = job
        return job

    def get_by_id(self, job_id: str) -> AvatarJob | None:
        return self.jobs_by_id.get(job_id)

    def update(self, job: AvatarJob) -> AvatarJob:
        self.jobs_by_id[job.job_id] = job
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


class FixedClock(Clock):
    def __init__(self, *timestamps: datetime) -> None:
        self._timestamps = list(timestamps)

    def now(self) -> datetime:
        if len(self._timestamps) > 1:
            return self._timestamps.pop(0)
        return self._timestamps[0]


class FakeAvatarProvider:
    def __init__(self) -> None:
        self.should_fail = False
        self.failure_message = "Mock avatar provider failed."
        self.generated_jobs: list[str] = []

    def generate_video(self, job: AvatarJob) -> AvatarGeneratedVideo:
        self.generated_jobs.append(job.job_id)
        if self.should_fail:
            raise ExternalServiceError(
                self.failure_message,
                code="MOCK_PROVIDER_FAILURE",
            )
        return AvatarGeneratedVideo(content=b"mock-video", file_extension="mp4")


@pytest.fixture()
def validation_policy() -> AvatarValidationPolicy:
    return AvatarValidationPolicy(
        default_voice="Default Voice",
        max_script_length=300,
        max_image_size_bytes=5 * 1024 * 1024,
    )


def build_service(*, clock: FixedClock):
    repository = FakeRepository()
    storage = FakeStorage()
    observability = FakeObservability()
    provider = FakeAvatarProvider()
    service = AvatarGenerationService(
        repository=repository,
        asset_storage=storage,
        provider=provider,
        observability=observability,
        clock=clock,
        validation_policy=AvatarValidationPolicy(
            default_voice="Default Voice",
            max_script_length=300,
            max_image_size_bytes=5 * 1024 * 1024,
        ),
    )
    return service, repository, storage, observability, provider


def create_pending_job(
    service: AvatarGenerationService,
    repository: FakeRepository,
) -> AvatarJob:
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
            selected_voice="Default Voice",
        )
    )
    return repository.get_by_id(job.job_id) or job


def test_start_processing_moves_pending_job_to_processing() -> None:
    service, repository, _, observability, _ = build_service(
        clock=FixedClock(
            datetime(2026, 4, 16, 12, 0, tzinfo=UTC),
            datetime(2026, 4, 16, 12, 1, tzinfo=UTC),
        )
    )
    pending_job = create_pending_job(service, repository)

    processing_job = service.start_processing(pending_job.job_id)

    assert processing_job.status is AvatarJobStatus.PROCESSING
    assert processing_job.generated_video_path is None
    assert processing_job.provider_error_message is None
    assert observability.events[-1]["event"] == "avatar_job_status_changed"
    assert observability.events[-1]["previous_status"] == "pending"
    assert observability.events[-1]["new_status"] == "processing"


def test_complete_processing_stores_generated_video_only_for_complete_jobs() -> None:
    service, repository, storage, observability, provider = build_service(
        clock=FixedClock(
            datetime(2026, 4, 16, 12, 0, tzinfo=UTC),
            datetime(2026, 4, 16, 12, 1, tzinfo=UTC),
            datetime(2026, 4, 16, 12, 2, tzinfo=UTC),
        )
    )
    pending_job = create_pending_job(service, repository)
    processing_job = service.start_processing(pending_job.job_id)

    completed_job = service.complete_processing(processing_job.job_id)

    assert provider.generated_jobs == [pending_job.job_id]
    assert completed_job.status is AvatarJobStatus.COMPLETE
    assert completed_job.generated_video_path == f"videos/{pending_job.job_id}.mp4"
    assert completed_job.provider_error_message is None
    assert storage.saved_assets[-1] == (f"{pending_job.job_id}.mp4", b"mock-video", "videos")
    assert observability.events[-1]["event"] == "avatar_job_status_changed"
    assert observability.events[-1]["previous_status"] == "processing"
    assert observability.events[-1]["new_status"] == "complete"


def test_complete_processing_stores_provider_error_only_for_failed_jobs() -> None:
    service, repository, storage, observability, provider = build_service(
        clock=FixedClock(
            datetime(2026, 4, 16, 12, 0, tzinfo=UTC),
            datetime(2026, 4, 16, 12, 1, tzinfo=UTC),
            datetime(2026, 4, 16, 12, 2, tzinfo=UTC),
        )
    )
    provider.should_fail = True
    provider.failure_message = "Mock provider outage"
    pending_job = create_pending_job(service, repository)
    processing_job = service.start_processing(pending_job.job_id)

    failed_job = service.complete_processing(processing_job.job_id)

    assert failed_job.status is AvatarJobStatus.FAILED
    assert failed_job.generated_video_path is None
    assert failed_job.provider_error_message == "Mock provider outage"
    assert storage.saved_assets == [storage.saved_assets[0]]
    assert observability.events[-2]["event"] == "avatar_job_status_changed"
    assert observability.events[-2]["new_status"] == "failed"
    assert observability.events[-1]["event"] == "avatar_provider_failed"
    assert observability.events[-1]["failure_reason"] == "Mock provider outage"


def test_start_processing_raises_not_found_for_unknown_job() -> None:
    service, _, _, _, _ = build_service(
        clock=FixedClock(datetime(2026, 4, 16, 12, 0, tzinfo=UTC))
    )

    with pytest.raises(NotFoundError, match="was not found"):
        service.start_processing("missing-job")
