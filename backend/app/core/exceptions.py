"""
CarePath AI — Exception Handling
Consistent API error responses across the application.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class CarePathError(Exception):
    """Base exception for CarePath AI."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(CarePathError):
    """Resource not found."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} with identifier '{identifier}' not found.",
            status_code=404,
        )


class ValidationError(CarePathError):
    """Request validation failed."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=422,
            details=details or {},
        )


class ModelNotAvailableError(CarePathError):
    """ML model is not loaded or available."""

    def __init__(self, model_name: str = "wait_time"):
        super().__init__(
            code="MODEL_NOT_AVAILABLE",
            message=f"ML model '{model_name}' is not currently available.",
            status_code=503,
        )


class ConflictError(CarePathError):
    """Resource conflict (e.g., duplicate)."""

    def __init__(self, message: str):
        super().__init__(
            code="CONFLICT",
            message=message,
            status_code=409,
        )


class ServiceUnavailableError(CarePathError):
    """External service or dependency unavailable."""

    def __init__(self, service: str):
        super().__init__(
            code="SERVICE_UNAVAILABLE",
            message=f"Service '{service}' is currently unavailable.",
            status_code=503,
        )


class ForbiddenError(CarePathError):
    """Insufficient permissions."""

    def __init__(self, message: str = "Insufficient permissions for this action."):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=403,
        )


class RateLimitError(CarePathError):
    """Rate limit exceeded."""

    def __init__(self):
        super().__init__(
            code="RATE_LIMIT_EXCEEDED",
            message="Rate limit exceeded. Please try again later.",
            status_code=429,
        )


# ── FastAPI Exception Handlers ───────────────────────────────

async def carepath_exception_handler(request: Request, exc: CarePathError) -> JSONResponse:
    """Handle CarePathError exceptions with consistent JSON format."""
    from app.core.logging import get_logger, get_request_id

    logger = get_logger("error_handler")
    logger.warning(
        "carepath_error",
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        path=str(request.url.path),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": get_request_id(),
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    import traceback
    from app.core.logging import get_logger, get_request_id

    logger = get_logger("error_handler")
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=str(request.url.path),
    )
    # Print full traceback to stdout during development
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "request_id": get_request_id(),
            }
        },
    )
