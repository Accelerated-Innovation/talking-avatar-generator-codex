"""Observability port used by domain services."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Protocol


class ObservabilityPort(Protocol):
    """Outbound port for logs, spans, and counters."""

    def record_event(
        self,
        event: str,
        *,
        level: str = "info",
        **attributes: Any,
    ) -> None:
        """Record a structured event."""

    @contextmanager
    def start_span(
        self,
        name: str,
        *,
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[None]:
        """Start a trace span around a domain operation."""
        yield None

    def increment_counter(
        self,
        name: str,
        value: int = 1,
        *,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Increment a named counter."""
