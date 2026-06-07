# apps/platforms/middleware.py
import logging

from django.http import JsonResponse

from apps.platforms.models import College, CollegeStatus

logger = logging.getLogger(__name__)


class TenantResolutionMiddleware:
    """
    Resolves the current college tenant and attaches it to every request as
    ``request.college``.

    Resolution order (first match wins):
        1. HTTP header  ``X-College-ID``  (UUID of the college — useful for
           API clients, mobile apps, and Postman testing)
        2. Subdomain   ``<slug>.cms.example.com``  (production browser flow)

    If no college is resolved, ``request.college`` is set to ``None``.
    Endpoints that *require* a tenant (i.e. all college-scoped views) must
    check this via the ``IsTenantResolved`` permission or
    ``CollegeScopedMixin``.

    Platform-wide endpoints (SuperUser admin, plan management) work fine with
    ``request.college = None``.
    """

    HEADER_NAME = "HTTP_X_COLLEGE_ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.college = self._resolve_college(request)
        return self.get_response(request)

    def _resolve_college(self, request):
        # --- 1. Header-based resolution ---
        college_id = request.META.get(self.HEADER_NAME)
        if college_id:
            try:
                return College.objects.get(id=college_id, status=CollegeStatus.ACTIVE)
            except (College.DoesNotExist, Exception):
                logger.warning("TenantMiddleware: invalid X-College-ID header: %s", college_id)
                return None

        # --- 2. Subdomain-based resolution ---
        host = request.get_host().split(":")[0]   # strip port
        parts = host.split(".")
        if len(parts) >= 3:
            subdomain = parts[0]
            try:
                return College.objects.get(
                    subdomain=subdomain,
                    status=CollegeStatus.ACTIVE,
                )
            except College.DoesNotExist:
                pass

        return None
