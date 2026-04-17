"""Unit tests for avatar job detail query behavior."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from common.errors import NotFoundError
from services.avatar_generation.models import AvatarJob, AvatarJobStatus
from services.avatar_generation.query_service import AvatarJobQueryService


class FakeRepository:
    def __init__(self, jobs: dict[str, AvatarJob] | None = None) -> None:
        self.jobs = jobs or {}

    def create(self, job: AvatarJob) -> AvatarJob:
        self.jobs[job.job_id] = job
        return job

    def get_by_id(self, job_id: str) -> AvatarJob | None:
        return self.jobs.get(job_id)

    def update(self, job: AvatarJob) -> AvatarJob:
        self.jobs[job.job_id] = job
        return job


def build_job(
    *,
    job_id: str = "job-123",
    status: AvatarJobStatus = AvatarJobStatus.PENDING,
    generated_video_path: str | None = None,
    provider_error_message: str | None = None,
) -> AvatarJob:
    timestamp = datetime(2026, 4, 17, tzinfo=UTC)
    return AvatarJob(
        job_id=job_id,
        script="Hello avatar",
        voice="Default Voice",
        status=status,
        image_path="portraits/job-123.png",
        created_at=timestamp,
        updated_at=timestamp,
        generated_video_path=generated_video_path,
        provider_error_message=provider_error_message,
    )


def test_get_avatar_job_detail_returns_complete_job_with_video() -> None:
    repository = FakeRepository(
        jobs={
            "job-123": build_job(
                status=AvatarJobStatus.COMPLETE,
                generated_video_path="videos/job-123.mp4",
            )
        }
    )
    service = AvatarJobQueryService(repository=repository)

    detail = service.get_avatar_job_detail("job-123")

    assert detail.job_id == "job-123"
    assert detail.status == "complete"
    assert detail.generated_video_path == "videos/job-123.mp4"
    assert detail.show_generated_video is True


def test_get_avatar_job_detail_hides_video_for_non_complete_jobs() -> None:
    repository = FakeRepository(
        jobs={
            "job-123": build_job(
                status=AvatarJobStatus.PROCESSING,
                generated_video_path=None,
            )
        }
    )
    service = AvatarJobQueryService(repository=repository)

    detail = service.get_avatar_job_detail("job-123")

    assert detail.status == "processing"
    assert detail.generated_video_path is None
    assert detail.show_generated_video is False


def test_get_avatar_job_detail_preserves_failure_reason_for_failed_jobs() -> None:
    repository = FakeRepository(
        jobs={
            "job-123": build_job(
                status=AvatarJobStatus.FAILED,
                provider_error_message="Mock provider outage",
            )
        }
    )
    service = AvatarJobQueryService(repository=repository)

    detail = service.get_avatar_job_detail("job-123")

    assert detail.status == "failed"
    assert detail.provider_error_message == "Mock provider outage"
    assert detail.show_generated_video is False


def test_get_avatar_job_detail_raises_not_found_for_unknown_job() -> None:
    service = AvatarJobQueryService(repository=FakeRepository())

    with pytest.raises(NotFoundError, match="was not found"):
        service.get_avatar_job_detail("missing-job")
