"""Query service for avatar job detail rendering."""

from __future__ import annotations

from common.errors import NotFoundError
from ports.inbound.avatar_job_query import AvatarJobQueryPort
from ports.outbound.avatar_job_repository import AvatarJobRepositoryPort
from services.avatar_generation.models import AvatarJob, AvatarJobStatus
from services.avatar_generation.query_models import AvatarJobDetailView


class AvatarJobQueryService(AvatarJobQueryPort):
    """Loads avatar job details and shapes them for display."""

    def __init__(self, repository: AvatarJobRepositoryPort) -> None:
        self._repository = repository

    def get_avatar_job_detail(self, job_id: str) -> AvatarJobDetailView:
        """Return a shaped detail view or raise not found."""

        job = self._repository.get_by_id(job_id)
        if job is None:
            raise NotFoundError(
                f"Avatar job {job_id} was not found.",
                code="AVATAR_JOB_NOT_FOUND",
            )
        return self._to_detail_view(job)

    def _to_detail_view(self, job: AvatarJob) -> AvatarJobDetailView:
        show_generated_video = (
            job.status is AvatarJobStatus.COMPLETE
            and job.generated_video_path is not None
        )
        return AvatarJobDetailView(
            job_id=job.job_id,
            status=job.status.value,
            script=job.script,
            voice=job.voice,
            image_path=job.image_path,
            generated_video_path=job.generated_video_path if show_generated_video else None,
            provider_error_message=job.provider_error_message,
            show_generated_video=show_generated_video,
        )
