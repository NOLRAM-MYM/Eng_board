"""
apps/core/responses.py
=======================
Standardised JSON response helpers and a custom DRF exception handler.

All API responses follow this envelope structure:

    Success:
    {
        "status": "success",
        "data": { ... }
    }

    Error:
    {
        "status": "error",
        "code": "validation_error",
        "message": "Human-readable summary",
        "errors": { "field": ["detail", ...] }
    }
"""

import logging
from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response Builders
# ---------------------------------------------------------------------------

def success_response(data: Any, http_status: int = status.HTTP_200_OK) -> Response:
    """
    Return a standardised success Response.

    Args:
        data:        Serializable payload to nest under ``"data"``.
        http_status: HTTP status code (default 200).

    Returns:
        DRF ``Response`` with ``{"status": "success", "data": ...}``.
    """
    return Response(
        {"status": "success", "data": data},
        status=http_status,
    )


def error_response(
    message: str,
    code: str = "error",
    errors: dict | None = None,
    http_status: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    """
    Return a standardised error Response.

    Args:
        message:     Human-readable error summary.
        code:        Machine-readable error code (e.g. ``"validation_error"``).
        errors:      Optional field-level error details.
        http_status: HTTP status code (default 400).

    Returns:
        DRF ``Response`` with structured error envelope.
    """
    payload: dict = {
        "status": "error",
        "code": code,
        "message": message,
    }
    if errors:
        payload["errors"] = errors
    return Response(payload, status=http_status)


# ---------------------------------------------------------------------------
# Custom DRF Exception Handler
# ---------------------------------------------------------------------------

def custom_exception_handler(exc: Exception, context: dict) -> Response | None:
    """
    Wrap DRF's default exception handler output in our standard envelope.

    Configured in ``settings/base.py`` under ``REST_FRAMEWORK['EXCEPTION_HANDLER']``.
    """
    # Let DRF handle the exception first
    response = drf_exception_handler(exc, context)

    if response is not None:
        # Log server errors with full traceback
        if response.status_code >= 500:
            logger.exception(
                "Unhandled API exception in %s",
                context.get('view', 'unknown view'),
                exc_info=exc,
            )

        # Re-shape the response into our envelope
        original_data = response.data

        # Determine human-readable message
        if isinstance(original_data, dict):
            # DRF ValidationError: {"field": ["error"]}
            message = _extract_message(original_data)
            errors = original_data
        elif isinstance(original_data, list):
            message = str(original_data[0]) if original_data else "An error occurred."
            errors = {"non_field_errors": original_data}
        else:
            message = str(original_data)
            errors = None

        response.data = {
            "status": "error",
            "code": _status_to_code(response.status_code),
            "message": message,
            "errors": errors,
        }

    return response


# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _extract_message(data: dict) -> str:
    """Extract first human-readable message from a DRF validation error dict."""
    for key, value in data.items():
        if isinstance(value, list) and value:
            return f"{key}: {value[0]}"
        if isinstance(value, str):
            return f"{key}: {value}"
    return "Validation failed."


def _status_to_code(http_status: int) -> str:
    """Map HTTP status code to a machine-readable error code string."""
    codes = {
        400: "validation_error",
        401: "authentication_required",
        403: "permission_denied",
        404: "not_found",
        405: "method_not_allowed",
        429: "throttled",
        500: "server_error",
    }
    return codes.get(http_status, "error")
