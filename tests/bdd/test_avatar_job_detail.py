"""BDD tests for Increment 3 avatar job detail behavior."""

from __future__ import annotations

from io import BytesIO

from PIL import Image
from pytest_bdd import given, parsers, scenario, then, when

from services.avatar_generation.models import AvatarJobStatus


@scenario(
    "../../features/talking_avatar_generator/acceptance.feature",
    "View a completed avatar result",
)
def test_view_completed_avatar_result():
    """Completed jobs render their video and submission details."""


@scenario(
    "../../features/talking_avatar_generator/acceptance.feature",
    "Show processing status while avatar generation is in progress",
)
def test_show_processing_status_while_generation_is_in_progress():
    """Processing jobs show status without a video."""


@scenario(
    "../../features/talking_avatar_generator/acceptance.feature",
    "Return not found when the user requests an unknown avatar job",
)
def test_return_not_found_when_requesting_unknown_job():
    """Unknown jobs return the standardized not-found response."""


@scenario(
    "../../features/talking_avatar_generator/acceptance.feature",
    "Display submission details for a completed avatar job",
)
def test_display_submission_details_for_completed_job():
    """Completed jobs show all submission metadata."""


@scenario(
    "../../features/talking_avatar_generator/acceptance.feature",
    "Do not display a generated video when the avatar job is not complete",
)
def test_do_not_display_generated_video_when_job_not_complete():
    """Pending jobs do not render a generated video."""


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


@given("an avatar job exists with status \"complete\"")
def avatar_job_exists_complete(client, app, detail_context):
    response = client.post(
        "/v1/avatar-jobs",
        data={"script": "Hello avatar", "voice": "Default Voice"},
        files={"image": ("portrait.png", build_image_bytes("PNG"), "image/png")},
    )
    job_id = response.json()["data"]["job_id"]
    app.state.avatar_provider.configure_success()
    app.state.avatar_processing_port.start_processing(job_id)
    detail_context["job"] = app.state.avatar_processing_port.complete_processing(job_id)
    detail_context["job_id"] = job_id
    assert detail_context["job"].status is AvatarJobStatus.COMPLETE


@given("an avatar job exists with status \"processing\"")
def avatar_job_exists_processing(client, app, detail_context):
    response = client.post(
        "/v1/avatar-jobs",
        data={"script": "Hello avatar", "voice": "Default Voice"},
        files={"image": ("portrait.png", build_image_bytes("PNG"), "image/png")},
    )
    job_id = response.json()["data"]["job_id"]
    detail_context["job"] = app.state.avatar_processing_port.start_processing(job_id)
    detail_context["job_id"] = job_id
    assert detail_context["job"].status is AvatarJobStatus.PROCESSING


@given("an avatar job exists with status \"pending\"")
def avatar_job_exists_pending(client, detail_context):
    response = client.post(
        "/v1/avatar-jobs",
        data={"script": "Hello avatar", "voice": "Default Voice"},
        files={"image": ("portrait.png", build_image_bytes("PNG"), "image/png")},
    )
    detail_context["job_id"] = response.json()["data"]["job_id"]


@given("the avatar job has a generated video path")
def avatar_job_has_generated_video_path(app, detail_context):
    job = app.state.avatar_job_repository.get_by_id(detail_context["job_id"])
    assert job is not None
    assert job.generated_video_path is not None


@given("no avatar job exists for the requested identifier")
def no_avatar_job_exists(detail_context):
    detail_context["job_id"] = "missing-job"


@when("I open the avatar job detail page")
@when("I request the avatar job detail page")
def open_avatar_job_detail_page(client, detail_context):
    detail_context["response"] = client.get(f"/v1/avatar-jobs/{detail_context['job_id']}")


@then("I should see the original portrait image")
def should_see_original_portrait_image(detail_context):
    assert "portraits/" in detail_context["response"].text


@then("I should see the submitted script")
def should_see_submitted_script(detail_context):
    assert "Hello avatar" in detail_context["response"].text


@then("I should see the selected voice")
def should_see_selected_voice(detail_context):
    assert "Default Voice" in detail_context["response"].text


@then("I should see the generated avatar video")
def should_see_generated_avatar_video(detail_context):
    assert "videos/" in detail_context["response"].text
    assert "<video" in detail_context["response"].text


@then("I should see the avatar job status as \"processing\"")
def should_see_processing_status(detail_context):
    assert "processing" in detail_context["response"].text


@then("I should not see a generated avatar video yet")
@then("I should not see a generated avatar video")
def should_not_see_generated_avatar_video(detail_context):
    assert "<video" not in detail_context["response"].text
    assert "videos/" not in detail_context["response"].text


@then("the system should return not found")
def system_should_return_not_found(detail_context):
    response = detail_context["response"]
    assert response.status_code == 404
    payload = response.json()
    assert payload["data"] is None
    assert payload["error"]["code"] == "AVATAR_JOB_NOT_FOUND"


@then("I should see the avatar job identifier")
def should_see_avatar_job_identifier(detail_context):
    assert detail_context["job_id"] in detail_context["response"].text


@then("I should see the current avatar job status")
def should_see_current_avatar_job_status(detail_context):
    assert "complete" in detail_context["response"].text
