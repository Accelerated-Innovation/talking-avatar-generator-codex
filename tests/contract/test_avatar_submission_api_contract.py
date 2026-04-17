"""Contract tests for the avatar submission API route."""

from __future__ import annotations

from io import BytesIO

from PIL import Image


def create_image_bytes(image_format: str) -> bytes:
    image = Image.new("RGB", (2, 2), color=(255, 0, 0))
    buffer = BytesIO()
    image.save(buffer, format=image_format)
    return buffer.getvalue()


def test_create_avatar_job_returns_standard_envelope_on_success(client) -> None:
    response = client.post(
        "/v1/avatar-jobs",
        data={"script": "Hello avatar", "voice": "Default Voice"},
        files={"image": ("portrait.png", create_image_bytes("PNG"), "image/png")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert set(payload.keys()) == {"data", "error"}
    assert payload["error"] is None
    assert payload["data"]["status"] == "pending"
    assert payload["data"]["voice"] == "Default Voice"
    assert payload["data"]["script"] == "Hello avatar"
    assert payload["data"]["image_path"].startswith("portraits/")


def test_create_avatar_job_returns_standard_error_envelope_on_validation_failure(client) -> None:
    response = client.post(
        "/v1/avatar-jobs",
        data={"script": "", "voice": "Default Voice"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["data"] is None
    assert payload["error"]["code"] == "MISSING_IMAGE"
    assert "portrait image is required" in payload["error"]["message"]
