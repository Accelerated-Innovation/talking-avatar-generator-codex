"""Shared pytest fixtures for the talking avatar feature."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.app import create_app
from common.settings import AppSettings


@pytest.fixture()
def app_settings(tmp_path: Path) -> AppSettings:
    """Create isolated settings for each test."""

    return AppSettings(
        database_url=f"sqlite:///{tmp_path / 'talking-avatar.db'}",
        asset_dir=tmp_path / "assets",
    )


@pytest.fixture()
def app(app_settings: AppSettings):
    """Create the FastAPI app for tests."""

    return create_app(settings=app_settings)


@pytest.fixture()
def client(app) -> TestClient:
    """Return a synchronous test client."""

    return TestClient(app)
