"""BDD tests for Increment 1 submission scenarios."""

from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image
from pytest_bdd import given, parsers, scenario, then, when


@scenario(
    "../../features/talking_avatar_generator/acceptance.feature",
    "Submit a valid avatar generation request with the default voice",
)
def test_submit_valid_avatar_generation_request():
    """Happy-path submission."""


@scenario(
    "../../features/talking_avatar_generator/acceptance.feature",
    "Create an avatar job only after validation passes",
)
def test_create_avatar_job_only_after_validation_passes():
    """Persist a new pending avatar job only when validation succeeds."""


@scenario(
    "../../features/talking_avatar_generator/acceptance.feature",
    "Reject a submission when no image is provided",
)
def test_reject_submission_when_no_image_is_provided():
    """Reject missing image input."""


@scenario(
    "../../features/talking_avatar_generator/acceptance.feature",
    "Reject a submission when the image type is not supported",
)
def test_reject_submission_when_image_type_is_not_supported():
    """Reject unsupported file types."""


@scenario(
    "../../features/talking_avatar_generator/acceptance.feature",
    "Reject a submission when the image exceeds the maximum size",
)
def test_reject_submission_when_image_exceeds_max_size():
    """Reject oversized uploads."""


@scenario(
    "../../features/talking_avatar_generator/acceptance.feature",
    "Reject a submission when no script is provided",
)
def test_reject_submission_when_no_script_is_provided():
    """Reject missing script input."""


@scenario(
    "../../features/talking_avatar_generator/acceptance.feature",
    "Reject a submission when the script exceeds the maximum length",
)
def test_reject_submission_when_script_exceeds_max_length():
    """Reject overlong scripts."""


@pytest.fixture()
def context():
    return {
        "form": {"script": "", "voice": "Default Voice"},
        "files": None,
        "response": None,
    }


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
def default_voice(context, voice: str):
    context["form"]["voice"] = voice


@given(parsers.parse("the maximum script length is {max_length:d} characters"))
def max_script_length(context, max_length: int):
    context["max_script_length"] = max_length


@given("supported image types are jpg, jpeg, and png")
def supported_image_types(context):
    context["supported_types"] = {"jpg", "jpeg", "png"}


@given("the maximum image size is 5 MB")
def max_image_size(context):
    context["max_image_size_bytes"] = 5 * 1024 * 1024


@given("I am on the avatar submission page")
def on_submission_page(client):
    response = client.get("/v1/avatar-jobs/new")
    assert response.status_code == 200


@when("I upload a valid png portrait image")
def upload_valid_png(context):
    context["files"] = {
        "image": ("portrait.png", build_image_bytes("PNG"), "image/png"),
    }


@when("I upload a valid jpg portrait image")
def upload_valid_jpg(context):
    context["files"] = {
        "image": ("portrait.jpg", build_image_bytes("JPEG"), "image/jpeg"),
    }


@when("I upload a valid jpeg portrait image")
def upload_valid_jpeg(context):
    context["files"] = {
        "image": ("portrait.jpeg", build_image_bytes("JPEG"), "image/jpeg"),
    }


@when("I upload a portrait image with an unsupported file type")
def upload_unsupported_image(context):
    context["files"] = {
        "image": ("portrait.gif", b"GIF89a", "image/gif"),
    }


@when("I upload a portrait image larger than 5 MB")
def upload_oversized_image(context):
    context["files"] = {
        "image": ("portrait.png", b"a" * ((5 * 1024 * 1024) + 1), "image/png"),
    }


@when("I enter a script that is 300 characters or fewer")
@when("I enter a valid script")
def enter_valid_script(context):
    context["form"]["script"] = "Hello avatar"


@when("I enter a script longer than 300 characters")
def enter_long_script(context):
    context["form"]["script"] = "x" * 301


@when("I submit the avatar generation request")
def submit_request(client, context):
    context["response"] = client.post(
        "/v1/avatar-jobs",
        data=context["form"],
        files=context["files"],
    )


@when("I submit the avatar generation request without an image")
def submit_without_image(client, context):
    context["response"] = client.post(
        "/v1/avatar-jobs",
        data=context["form"],
    )


@when("I submit the avatar generation request without a script")
def submit_without_script(client, context):
    form = {**context["form"], "script": ""}
    context["response"] = client.post(
        "/v1/avatar-jobs",
        data=form,
        files=context["files"],
    )


@then("the system should accept the request")
def system_accepts_request(context):
    assert context["response"].status_code == 201


@then("the system should create a new avatar job")
def system_creates_new_job(context):
    payload = context["response"].json()
    assert payload["data"]["job_id"]


@then("the avatar job should use the default voice")
def avatar_job_uses_default_voice(context):
    payload = context["response"].json()
    assert payload["data"]["voice"] == "Default Voice"


@then(parsers.parse('the avatar job status should be "{status}"'))
def avatar_job_status_matches(context, status: str):
    payload = context["response"].json()
    assert payload["data"]["status"] == status


@then("the system should create a unique avatar job identifier")
def create_unique_identifier(context):
    payload = context["response"].json()
    assert payload["data"]["job_id"]


@then("the system should store the submitted image reference")
def stores_image_reference(context):
    payload = context["response"].json()
    assert payload["data"]["image_path"].startswith("portraits/")


@then("the system should store the submitted script")
def stores_script(context):
    payload = context["response"].json()
    assert payload["data"]["script"] == context["form"]["script"]


@then("the system should store the selected voice")
def stores_selected_voice(context):
    payload = context["response"].json()
    assert payload["data"]["voice"] == context["form"]["voice"]


@then("the system should reject the request")
def system_rejects_request(context):
    assert context["response"].status_code == 422


@then("I should see a validation message for the missing image")
def validation_message_missing_image(context):
    payload = context["response"].json()
    assert "portrait image is required" in payload["error"]["message"]


@then("I should see a validation message for unsupported image type")
def validation_message_unsupported_type(context):
    payload = context["response"].json()
    assert payload["error"]["code"] == "UNSUPPORTED_IMAGE_TYPE"


@then("I should see a validation message for image size")
def validation_message_image_size(context):
    payload = context["response"].json()
    assert payload["error"]["code"] == "IMAGE_TOO_LARGE"


@then("I should see a validation message for the missing script")
def validation_message_missing_script(context):
    payload = context["response"].json()
    assert payload["error"]["code"] == "MISSING_SCRIPT"


@then("I should see a validation message for script length")
def validation_message_script_length(context):
    payload = context["response"].json()
    assert payload["error"]["code"] == "SCRIPT_TOO_LONG"


@then("no avatar job should be created")
def no_avatar_job_created(app):
    assert app.state.avatar_job_repository.count() == 0
