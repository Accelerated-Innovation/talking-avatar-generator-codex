"""Domain error hierarchy shared across layers."""

from __future__ import annotations

from typing import Any


class DomainError(Exception):
    """Base class for domain-facing errors."""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


class ValidationError(DomainError):
    """Raised when business validation rules are violated."""


class NotFoundError(DomainError):
    """Raised when the requested entity cannot be located."""


class ConflictError(DomainError):
    """Raised when an operation conflicts with current state."""


class ExternalServiceError(DomainError):
    """Raised when an outbound dependency fails."""


class RateLimitError(DomainError):
    """Raised when a caller exceeds allowed throughput."""
