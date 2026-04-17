"""Domain services for avatar job submission and lifecycle behavior."""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from common.errors import ConflictError, ExternalServiceError, NotFoundError
from ports.inbound.avatar_processing import AvatarProcessingPort
from ports.inbound.avatar_submission import AvatarSubmissionInput, AvatarSubmissionPort
from ports.outbound.avatar_asset_storage import AvatarAssetStoragePort
from ports.outbound.avatar_job_repository import AvatarJobRepositoryPort
from ports.outbound.avatar_provider import AvatarProviderPort
from ports.outbound.clock import Clock
from ports.outbound.observability import ObservabilityPort
from services.avatar_generation.models import (
    AvatarJob,
    AvatarJobStatus,
    AvatarValidationPolicy,
)
from services.avatar_generation.validation import validate_submission_inputs


class AvatarGenerationService(AvatarSubmissionPort, AvatarProcessingPort):
    """Handles avatar submission validation and pending-job creation."""

    def __init__(
        self,
        repository: AvatarJobRepositoryPort,
        asset_storage: AvatarAssetStoragePort,
        provider: AvatarProviderPort,
        observability: ObservabilityPort,
        clock: Clock,
        validation_policy: AvatarValidationPolicy,
    ) -> None:
        self._repository = repository
        self._asset_storage = asset_storage
        self._provider = provider
        self._observability = observability
        self._clock = clock
        self._validation_policy = validation_policy

    def create_avatar_job(self, submission: AvatarSubmissionInput) -> AvatarJob:
        """Validate and persist a new pending avatar job."""

        normalized_script, detected_image_type = validate_submission_inputs(
            original_filename=submission.original_filename,
            declared_content_type=submission.declared_content_type,
            image_bytes=submission.image_bytes,
            script=submission.script,
            policy=self._validation_policy,
        )

        job_id = str(uuid4())
        normalized_voice = (
            (submission.selected_voice or "").strip()
            or self._validation_policy.default_voice
        )
        generated_filename = f"{job_id}.{'jpg' if detected_image_type == 'jpeg' else detected_image_type}"
        image_path = self._asset_storage.save_asset(
            generated_filename,
            submission.image_bytes or b"",
            category="portraits",
        )
        timestamp = self._clock.now()
        job = AvatarJob(
            job_id=job_id,
            script=normalized_script,
            voice=normalized_voice,
            status=AvatarJobStatus.PENDING,
            image_path=image_path,
            created_at=timestamp,
            updated_at=timestamp,
        )
        persisted_job = self._repository.create(job)
        self._observability.record_event(
            "avatar_job_created",
            job_id=persisted_job.job_id,
            status=persisted_job.status.value,
            timestamp=persisted_job.created_at.isoformat(),
        )
        return persisted_job

    def start_processing(self, job_id: str) -> AvatarJob:
        """Move a pending job into the processing state."""

        job = self._get_job(job_id)
        if job.status is not AvatarJobStatus.PENDING:
            raise ConflictError(
                f"Avatar job {job_id} cannot start processing from status {job.status.value}.",
                code="INVALID_JOB_STATUS",
            )

        timestamp = self._clock.now()
        processing_job = replace(
            job,
            status=AvatarJobStatus.PROCESSING,
            updated_at=timestamp,
            generated_video_path=None,
            provider_error_message=None,
        )
        persisted_job = self._repository.update(processing_job)
        self._record_status_transition(
            job_id=job.job_id,
            previous_status=job.status,
            new_status=persisted_job.status,
            timestamp=timestamp,
        )
        return persisted_job

    def complete_processing(self, job_id: str) -> AvatarJob:
        """Complete processing by storing a generated clip or a failure reason."""

        job = self._get_job(job_id)
        if job.status is not AvatarJobStatus.PROCESSING:
            raise ConflictError(
                f"Avatar job {job_id} cannot complete processing from status {job.status.value}.",
                code="INVALID_JOB_STATUS",
            )

        try:
            generated_video = self._provider.generate_video(job)
        except ExternalServiceError as exc:
            timestamp = self._clock.now()
            failed_job = replace(
                job,
                status=AvatarJobStatus.FAILED,
                updated_at=timestamp,
                generated_video_path=None,
                provider_error_message=str(exc),
            )
            persisted_job = self._repository.update(failed_job)
            self._record_status_transition(
                job_id=job.job_id,
                previous_status=job.status,
                new_status=persisted_job.status,
                timestamp=timestamp,
            )
            self._observability.record_event(
                "avatar_provider_failed",
                job_id=job.job_id,
                failure_reason=str(exc),
                timestamp=timestamp.isoformat(),
            )
            return persisted_job

        video_path = self._asset_storage.save_asset(
            f"{job.job_id}.{generated_video.file_extension}",
            generated_video.content,
            category="videos",
        )
        timestamp = self._clock.now()
        completed_job = replace(
            job,
            status=AvatarJobStatus.COMPLETE,
            updated_at=timestamp,
            generated_video_path=video_path,
            provider_error_message=None,
        )
        persisted_job = self._repository.update(completed_job)
        self._record_status_transition(
            job_id=job.job_id,
            previous_status=job.status,
            new_status=persisted_job.status,
            timestamp=timestamp,
        )
        return persisted_job

    def _get_job(self, job_id: str) -> AvatarJob:
        job = self._repository.get_by_id(job_id)
        if job is None:
            raise NotFoundError(
                f"Avatar job {job_id} was not found.",
                code="AVATAR_JOB_NOT_FOUND",
            )
        return job

    def _record_status_transition(
        self,
        *,
        job_id: str,
        previous_status: AvatarJobStatus,
        new_status: AvatarJobStatus,
        timestamp,
    ) -> None:
        self._observability.record_event(
            "avatar_job_status_changed",
            job_id=job_id,
            previous_status=previous_status.value,
            new_status=new_status.value,
            timestamp=timestamp.isoformat(),
        )
