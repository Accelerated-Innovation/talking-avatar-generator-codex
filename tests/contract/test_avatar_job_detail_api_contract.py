"""Contract tests for the avatar job detail route."""

from __future__ import annotations

from io import BytesIO

from PIL import Image


def create_image_bytes(image_format: str) -> bytes:
    image = Image.new("RGB", (2, 2), color=(255, 0, 0))
    buffer = BytesIO()
    image.save(buffer, format=image_format)
    return buffer.getvalue()


def create_completed_job(client, app) -> str:
    response = client.post(
        "/v1/avatar-jobs",
        data={"script": "Hello avatar", "voice": "Default Voice"},
        files={"image": ("portrait.png", create_image_bytes("PNG"), "image/png")},
    )
    job_id = response.json()["data"]["job_id"]
    app.state.avatar_provider.configure_success()
    app.state.avatar_processing_port.start_processing(job_id)
    app.state.avatar_processing_port.complete_processing(job_id)
    return job_id


def test_get_avatar_job_detail_returns_html_on_success(client, app) -> None:
    job_id = create_completed_job(client, app)

    response = client.get(f"/v1/avatar-jobs/{job_id}")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert job_id in response.text
    assert "Hello avatar" in response.text
    assert "Default Voice" in response.text


def test_get_avatar_job_detail_returns_standard_error_envelope_on_not_found(client) -> None:
    response = client.get("/v1/avatar-jobs/missing-job")

    assert response.status_code == 404
    payload = response.json()
    assert payload["data"] is None
    assert payload["error"]["code"] == "AVATAR_JOB_NOT_FOUND"
    assert "was not found" in payload["error"]["message"]
