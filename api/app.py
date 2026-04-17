"""Application factory for the talking avatar feature."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from adapters.local_avatar_asset_storage import LocalAvatarAssetStorageAdapter
from adapters.logging_observability import LoggingObservabilityAdapter
from adapters.mock_avatar_provider import MockAvatarProviderAdapter
from adapters.sqlite_avatar_job_repository import SQLiteAvatarJobRepositoryAdapter
from adapters.system_clock import SystemClock
from api.avatar_jobs import router as avatar_jobs_router
from api.models import ApiResponse, ErrorInfo
from common.errors import DomainError
from common.settings import AppSettings
from ports.inbound.avatar_processing import AvatarProcessingPort
from ports.inbound.avatar_submission import AvatarSubmissionPort
from ports.outbound.avatar_provider import AvatarProviderPort
from services.avatar_generation.models import AvatarValidationPolicy
from services.avatar_generation.service import AvatarGenerationService

DOMAIN_TO_HTTP: dict[type[DomainError], int] = {}


async def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Translate domain errors into standard API responses."""

    del request
    status_code = 422
    if exc.__class__.__name__ == "NotFoundError":
        status_code = 404
    elif exc.__class__.__name__ == "ConflictError":
        status_code = 409
    elif exc.__class__.__name__ == "ExternalServiceError":
        status_code = 502
    elif exc.__class__.__name__ == "RateLimitError":
        status_code = 429

    payload = ApiResponse(
        data=None,
        error=ErrorInfo(
            code=exc.code or exc.__class__.__name__.upper(),
            message=str(exc),
            details=exc.details,
        ),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def create_app(
    *,
    settings: AppSettings | None = None,
    submission_port: AvatarSubmissionPort | None = None,
    processing_port: AvatarProcessingPort | None = None,
    provider: AvatarProviderPort | None = None,
) -> FastAPI:
    """Create and configure the FastAPI application."""

    resolved_settings = settings or AppSettings()
    repository = SQLiteAvatarJobRepositoryAdapter(resolved_settings.database_url)
    asset_storage = LocalAvatarAssetStorageAdapter(resolved_settings.asset_dir)
    resolved_provider = provider or MockAvatarProviderAdapter()
    observability = LoggingObservabilityAdapter()
    clock = SystemClock()
    validation_policy = AvatarValidationPolicy(
        default_voice=resolved_settings.default_voice,
        max_script_length=resolved_settings.max_script_length,
        max_image_size_bytes=resolved_settings.max_image_size_bytes,
    )
    generation_service = AvatarGenerationService(
        repository=repository,
        asset_storage=asset_storage,
        provider=resolved_provider,
        observability=observability,
        clock=clock,
        validation_policy=validation_policy,
    )
    resolved_submission_port = submission_port or generation_service
    resolved_processing_port = processing_port or generation_service

    app = FastAPI(title=resolved_settings.app_name)
    app.state.settings = resolved_settings
    app.state.avatar_submission_port = resolved_submission_port
    app.state.avatar_processing_port = resolved_processing_port
    app.state.avatar_provider = resolved_provider
    app.state.avatar_job_repository = repository
    app.include_router(avatar_jobs_router)
    app.add_exception_handler(DomainError, domain_exception_handler)
    return app
