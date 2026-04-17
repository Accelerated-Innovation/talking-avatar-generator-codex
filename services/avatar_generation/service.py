"""Domain services for avatar job submission and lifecycle behavior."""

from __future__ import annotations

from uuid import uuid4

from ports.inbound.avatar_submission import AvatarSubmissionPort
from ports.outbound.avatar_asset_storage import AvatarAssetStoragePort
from ports.outbound.avatar_job_repository import AvatarJobRepositoryPort
from ports.outbound.clock import Clock
from ports.outbound.observability import ObservabilityPort
from services.avatar_generation.models import (
    AvatarJob,
    AvatarJobStatus,
    AvatarSubmissionInput,
    AvatarValidationPolicy,
)
from services.avatar_generation.validation import validate_submission_inputs


class AvatarGenerationService(AvatarSubmissionPort):
    """Handles avatar submission validation and pending-job creation."""

    def __init__(
        self,
        repository: AvatarJobRepositoryPort,
        asset_storage: AvatarAssetStoragePort,
        observability: ObservabilityPort,
        clock: Clock,
        validation_policy: AvatarValidationPolicy,
    ) -> None:
        self._repository = repository
        self._asset_storage = asset_storage
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
