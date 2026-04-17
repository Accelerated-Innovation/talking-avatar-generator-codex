"""Logging-backed observability adapter."""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from ports.outbound.observability import ObservabilityPort


class LoggingObservabilityAdapter(ObservabilityPort):
    """Simple structured logging adapter using the standard library."""

    def __init__(self) -> None:
        self._logger = logging.getLogger("talking_avatar_generator")
        if not self._logger.handlers:
            logging.basicConfig(level=logging.INFO)

    def record_event(
        self,
        event: str,
        *,
        level: str = "info",
        **attributes: Any,
    ) -> None:
        """Emit a log event as serialized structured data."""

        payload = {
            "event": event,
            "layer": "adapter",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **attributes,
        }
        log_method = getattr(self._logger, level, self._logger.info)
        log_method(json.dumps(payload, sort_keys=True, default=str))

    @contextmanager
    def start_span(
        self,
        name: str,
        *,
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[None]:
        """Provide a lightweight no-op span interface."""

        self.record_event(
            "span_started",
            level="debug",
            span_name=name,
            attributes=attributes or {},
        )
        try:
            yield None
        finally:
            self.record_event(
                "span_finished",
                level="debug",
                span_name=name,
            )

    def increment_counter(
        self,
        name: str,
        value: int = 1,
        *,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Emit a lightweight counter update."""

        self.record_event(
            "counter_incremented",
            level="debug",
            counter_name=name,
            counter_value=value,
            tags=tags or {},
        )
