"""Submission validation helpers."""

from __future__ import annotations

import imghdr
from pathlib import Path

from common.errors import ValidationError
from services.avatar_generation.models import AvatarValidationPolicy

SUPPORTED_DECLARED_TYPES: dict[str, str] = {
    "image/jpg": "jpeg",
    "image/jpeg": "jpeg",
    "image/png": "png",
}


def normalize_extension(filename: str | None) -> str | None:
    """Return the lower-cased extension without a leading dot."""

    if not filename:
        return None
    suffix = Path(filename).suffix.lower().lstrip(".")
    return suffix or None


def normalize_detected_image_type(image_bytes: bytes) -> str | None:
    """Detect the actual image type from file content."""

    detected_type = imghdr.what(None, image_bytes)
    if detected_type == "jpg":
        return "jpeg"
    return detected_type


def validate_submission_inputs(
    *,
    original_filename: str | None,
    declared_content_type: str | None,
    image_bytes: bytes | None,
    script: str | None,
    policy: AvatarValidationPolicy,
) -> tuple[str, str]:
    """Validate submission inputs and return normalized script/image type."""

    if not image_bytes or not original_filename:
        raise ValidationError(
            "A portrait image is required.",
            code="MISSING_IMAGE",
        )

    normalized_script = (script or "").strip()
    if not normalized_script:
        raise ValidationError(
            "A script is required.",
            code="MISSING_SCRIPT",
        )

    if len(normalized_script) > policy.max_script_length:
        raise ValidationError(
            f"Script must be {policy.max_script_length} characters or fewer.",
            code="SCRIPT_TOO_LONG",
            details={"max_length": policy.max_script_length},
        )

    if len(image_bytes) > policy.max_image_size_bytes:
        raise ValidationError(
            f"Image must be {policy.max_image_size_bytes // (1024 * 1024)} MB or smaller.",
            code="IMAGE_TOO_LARGE",
            details={"max_bytes": policy.max_image_size_bytes},
        )

    extension = normalize_extension(original_filename)
    if extension not in policy.supported_extensions:
        raise ValidationError(
            "Unsupported image type. Supported types are jpg, jpeg, and png.",
            code="UNSUPPORTED_IMAGE_TYPE",
        )

    normalized_declared_type = (
        SUPPORTED_DECLARED_TYPES.get(declared_content_type.lower())
        if declared_content_type
        else None
    )
    if normalized_declared_type is None:
        raise ValidationError(
            "Unsupported image type. Supported types are jpg, jpeg, and png.",
            code="UNSUPPORTED_IMAGE_TYPE",
        )

    normalized_detected_type = normalize_detected_image_type(image_bytes)
    if normalized_detected_type not in {"jpeg", "png"}:
        raise ValidationError(
            "Uploaded file content is not a supported image.",
            code="INVALID_IMAGE_CONTENT",
        )

    expected_type = "jpeg" if extension in {"jpg", "jpeg"} else extension
    if normalized_declared_type != expected_type or normalized_detected_type != expected_type:
        raise ValidationError(
            "Uploaded file content does not match the declared image type.",
            code="IMAGE_TYPE_MISMATCH",
        )

    return normalized_script, normalized_detected_type
