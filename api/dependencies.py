"""FastAPI dependency helpers."""

from __future__ import annotations

from fastapi import Request

from common.settings import AppSettings
from ports.inbound.avatar_job_query import AvatarJobQueryPort
from ports.inbound.avatar_submission import AvatarSubmissionPort


def get_settings(request: Request) -> AppSettings:
    """Return the application settings from app state."""

    return request.app.state.settings


def get_avatar_submission_port(request: Request) -> AvatarSubmissionPort:
    """Return the submission service from app state."""

    return request.app.state.avatar_submission_port


def get_avatar_job_query_port(request: Request) -> AvatarJobQueryPort:
    """Return the detail-query service from app state."""

    return request.app.state.avatar_job_query_port
