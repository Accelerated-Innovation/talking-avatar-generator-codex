"""BDD tests for Increment 2 avatar job processing behavior."""

from __future__ import annotations

from io import BytesIO

from PIL import Image
from pytest_bdd import given, parsers, scenario, then, when

from services.avatar_generation.models import AvatarJobStatus


@scenario(
    "../../features/talking_avatar_generator/acceptance.feature",
    "Move an avatar job from pending to processing to complete",
)
def test_move_avatar_job_from_pending_to_processing_to_complete():
    """Processing succeeds through valid lifecycle states."""


@scenario(
    "../../features/talking_avatar_generator/acceptance.feature",
    "Show failed status when avatar generation fails",
)
def test_show_failed_status_when_avatar_generation_fails():
    """Processing failure moves the job to a failed terminal state."""


def build_image_bytes(image_format: str) -> bytes:
    image = Image.new("RGB", (2, 2), color=(0, 128, 255))
    buffer = BytesIO()
    image.save(buffer, format=image_format)
    return buffer.getvalue()


@given("the Talking Avatar Generation application is available")
def app_available(client):
    response = client.get("/v1/avatar-jobs/new")
    assert response.status_code == 200


@given(parsers.parse('the default voice is "{voice}"'))
def default_voice(app, voice: str):
    del app, voice


@given(parsers.parse("the maximum script length is {max_length:d} characters"))
def max_script_length(app, max_length: int):
    del app, max_length


@given("supported image types are jpg, jpeg, and png")
def supported_image_types(app):
    del app


@given("the maximum image size is 5 MB")
def max_image_size(app):
    del app


@given("an avatar job exists with status \"pending\"")
def avatar_job_exists_with_status_pending(client, app, processing_context):
    response = client.post(
        "/v1/avatar-jobs",
        data={"script": "Hello avatar", "voice": "Default Voice"},
        files={"image": ("portrait.png", build_image_bytes("PNG"), "image/png")},
    )
    payload = response.json()
    job_id = payload["data"]["job_id"]
    processing_context["job_id"] = job_id
    processing_context["job"] = app.state.avatar_job_repository.get_by_id(job_id)
    assert processing_context["job"] is not None
    assert processing_context["job"].status is AvatarJobStatus.PENDING


@given("the mock avatar provider is configured to succeed")
def mock_provider_configured_to_succeed(app):
    app.state.avatar_provider.configure_success()


@given("the mock avatar provider is configured to fail")
def mock_provider_configured_to_fail(app):
    app.state.avatar_provider.configure_failure("Mock provider outage")


@when("avatar generation processing starts for the job")
def avatar_generation_processing_starts(app, processing_context):
    job_id = processing_context["job_id"]
    processing_context["job"] = app.state.avatar_processing_port.start_processing(job_id)


@when("avatar generation processing completes successfully")
def avatar_generation_processing_completes_successfully(app, processing_context):
    job_id = processing_context["job_id"]
    processing_context["job"] = app.state.avatar_processing_port.complete_processing(job_id)


@when("avatar generation processing fails")
def avatar_generation_processing_fails(app, processing_context):
    job_id = processing_context["job_id"]
    processing_context["job"] = app.state.avatar_processing_port.complete_processing(job_id)


@then("the avatar job status should change to \"processing\"")
def avatar_job_status_changes_to_processing(processing_context):
    assert processing_context["job"].status is AvatarJobStatus.PROCESSING


@then("the avatar job status should change to \"complete\"")
def avatar_job_status_changes_to_complete(processing_context):
    assert processing_context["job"].status is AvatarJobStatus.COMPLETE


@then("the avatar job should store a generated video path")
def avatar_job_stores_generated_video_path(processing_context):
    assert processing_context["job"].generated_video_path
    assert processing_context["job"].generated_video_path.startswith("videos/")


@then("the avatar job status should change to \"failed\"")
def avatar_job_status_changes_to_failed(processing_context):
    assert processing_context["job"].status is AvatarJobStatus.FAILED


@then("the avatar job should store a provider error message")
def avatar_job_stores_provider_error_message(processing_context):
    assert processing_context["job"].provider_error_message == "Mock provider outage"
