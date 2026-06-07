# apps/platforms/exceptions.py
import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Wrap all DRF exceptions in a consistent envelope:
        {
            "success": false,
            "error": {
                "code": "permission_denied",
                "message": "...",
                "details": { ... }
            }
        }
    Unhandled exceptions are re-raised so Django's 500 handler logs them.
    """
    response = exception_handler(exc, context)

    if response is not None:
        status_code = response.status_code
        error_code = _status_to_code(status_code)

        # Flatten DRF's various error shapes into a single message string
        data = response.data
        if isinstance(data, dict):
            message = data.get("detail", str(data))
            details = {k: v for k, v in data.items() if k != "detail"}
        elif isinstance(data, list):
            message = " ".join(str(item) for item in data)
            details = {}
        else:
            message = str(data)
            details = {}

        response.data = {
            "success": False,
            "error": {
                "code": error_code,
                "message": str(message),
                "details": details or None,
            },
        }
    else:
        # Unexpected server-side exception — log it
        logger.exception("Unhandled exception in view: %s", exc)

    return response


def _status_to_code(status_code):
    return {
        400: "bad_request",
        401: "unauthenticated",
        403: "permission_denied",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        422: "unprocessable_entity",
        429: "throttled",
        500: "internal_server_error",
    }.get(status_code, f"http_{status_code}")
