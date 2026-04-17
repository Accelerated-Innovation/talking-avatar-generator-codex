"""Clock abstraction for deterministic time handling."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """Provides the current UTC timestamp."""

    def now(self) -> datetime:
        """Return the current UTC timestamp."""
