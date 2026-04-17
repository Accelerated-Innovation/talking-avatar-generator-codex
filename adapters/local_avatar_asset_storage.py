"""Local filesystem adapter for avatar assets."""

from __future__ import annotations

from pathlib import Path

from ports.outbound.avatar_asset_storage import AvatarAssetStoragePort


class LocalAvatarAssetStorageAdapter(AvatarAssetStoragePort):
    """Stores assets under a configured root directory."""

    def __init__(self, root_directory: Path) -> None:
        self._root_directory = root_directory

    def save_asset(self, filename: str, content: bytes, *, category: str) -> str:
        """Persist the provided content and return a relative asset path."""

        category_directory = self._root_directory / category
        category_directory.mkdir(parents=True, exist_ok=True)
        target_path = category_directory / filename
        target_path.write_bytes(content)
        return (Path(category) / filename).as_posix()
