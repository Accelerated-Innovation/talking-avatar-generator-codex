"""Avatar job submission routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from fastapi.templating import Jinja2Templates

from api.dependencies import get_avatar_submission_port, get_settings
from api.models import ApiResponse, AvatarJobResponse, AvatarSubmissionForm
from common.settings import AppSettings
from ports.inbound.avatar_submission import AvatarSubmissionPort
from services.avatar_generation.models import AvatarSubmissionInput

router = APIRouter(prefix="/v1/avatar-jobs", tags=["avatar-jobs"])
templates = Jinja2Templates(directory="templates")


@router.get(
    "/new",
    summary="Render the avatar submission page",
    description="Returns the HTML form used to submit a new talking avatar job.",
)
def get_avatar_submission_page(
    request: Request,
    settings: AppSettings = Depends(get_settings),
):
    """Render the submission page."""

    return templates.TemplateResponse(
        request=request,
        name="avatar_submission.html",
        context={
            "default_voice": settings.default_voice,
            "max_script_length": settings.max_script_length,
            "max_image_size_bytes": settings.max_image_size_bytes,
            "supported_image_types": "jpg, jpeg, png",
        },
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse,
    summary="Create a new avatar job",
    description="Validates portrait upload and script content, then persists a pending avatar job.",
)
async def create_avatar_job(
    request: Request,
    image: UploadFile | None = File(default=None, description="Portrait image upload"),
    script: str = Form(default=""),
    voice: str | None = Form(default=None),
    submission_port: AvatarSubmissionPort = Depends(get_avatar_submission_port),
):
    """Validate and persist a new pending avatar job."""

    form_model = AvatarSubmissionForm(script=script, voice=voice)
    image_bytes = await image.read() if image is not None else None
    job = submission_port.create_avatar_job(
        AvatarSubmissionInput(
            original_filename=image.filename if image is not None else None,
            declared_content_type=image.content_type if image is not None else None,
            image_bytes=image_bytes,
            script=form_model.script,
            selected_voice=form_model.voice,
        )
    )
    return ApiResponse(data=AvatarJobResponse.from_domain(job), error=None)
