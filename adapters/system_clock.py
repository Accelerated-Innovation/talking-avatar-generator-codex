"""System clock adapter."""

from __future__ import annotations

from datetime import UTC, datetime

from ports.outbound.clock import Clock


class SystemClock(Clock):
    """Returns the current UTC time."""

    def now(self) -> datetime:
        return datetime.now(UTC)
