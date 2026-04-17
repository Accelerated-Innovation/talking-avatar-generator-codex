"""Shared pytest fixtures for the talking avatar feature."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def app_settings(tmp_path: Path):
    """Create isolated settings for each test."""

    from common.settings import AppSettings

    return AppSettings(
        database_url=f"sqlite:///{tmp_path / 'talking-avatar.db'}",
        asset_dir=tmp_path / "assets",
    )


@pytest.fixture()
def app(app_settings):
    """Create the FastAPI app for tests."""

    from api.app import create_app

    return create_app(settings=app_settings)


@pytest.fixture()
def client(app) -> TestClient:
    """Return a synchronous test client."""

    return TestClient(app)


@pytest.fixture()
def processing_context():
    """Share processing state across BDD steps."""

    return {
        "job_id": None,
        "job": None,
    }
