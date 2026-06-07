# apps/audit/middleware.py
import json
import logging

from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)

_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# Paths we never want to audit (performance + noise)
_SKIP_PATHS = {"/api/auth/me/", "/admin/jsi18n/"}


class AuditLogMiddleware:
    """
    Automatically write an AuditLog entry for every mutating API request
    (POST / PUT / PATCH / DELETE) that results in a 2xx response.

    Captures:
      - actor (request.user)
      - college tenant (request.college)
      - HTTP action + path
      - response status code
      - request body (JSON only; files are skipped)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.method in _WRITE_METHODS
            and request.path not in _SKIP_PATHS
            and 200 <= response.status_code < 300
        ):
            self._write_log(request, response)

        return response

    def _write_log(self, request, response):
        try:
            user = request.user if request.user.is_authenticated else None
            college = getattr(request, "college", None)

            # Try to parse body as JSON; skip binary / form payloads
            payload = {}
            content_type = request.content_type or ""
            if "application/json" in content_type:
                try:
                    payload = json.loads(request.body)
                except Exception:
                    pass

            # Redact sensitive keys
            for key in ("password", "old_password", "new_password", "token", "secret"):
                if key in payload:
                    payload[key] = "***"

            AuditLog.objects.create(
                college=college,
                actor=user,
                action=f"{request.method} {request.path}",
                entity_type=self._extract_entity_type(request.path),
                entity_id=None,   # populated by per-model signals if needed
                payload=payload,
                ip_address=self._get_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
            )
        except Exception:
            logger.exception("AuditLogMiddleware: failed to write audit log")

    @staticmethod
    def _extract_entity_type(path):
        parts = [p for p in path.strip("/").split("/") if p]
        # e.g. /api/accounts/students/  → "students"
        return parts[-1] if parts else "unknown"

    @staticmethod
    def _get_ip(request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
