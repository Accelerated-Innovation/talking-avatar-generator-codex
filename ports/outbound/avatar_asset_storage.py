"""Outbound port for storing avatar assets."""

from __future__ import annotations

from typing import Protocol


class AvatarAssetStoragePort(Protocol):
    """Persists asset bytes and returns a stable relative path."""

    def save_asset(self, filename: str, content: bytes, *, category: str) -> str:
        """Save raw asset bytes into the requested category."""
