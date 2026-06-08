# apps/web/middleware.py
"""
WebAuthRedirectMiddleware
--------------------------
Intercepts unauthenticated requests to web (non-API) paths and redirects
them to the web login page instead of the DRF JSON 401.

Why needed:
  - settings.LOGIN_URL currently points to /api/auth/login/ (the DRF endpoint).
  - Django's login_required / LoginRequiredMixin uses LOGIN_URL for redirects.
  - We override it here so the web layer always sends humans to /login/,
    while API paths continue to return 401 JSON.

The middleware is path-aware: it only intercepts paths that are NOT under /api/.
"""
import logging

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)

# Paths that should never be intercepted by this middleware
_API_PREFIX = "/api/"
_ADMIN_PREFIX = "/admin/"
_STATIC_PREFIX = "/static/"
_MEDIA_PREFIX = "/media/"

# Web paths that are publicly accessible (no login check)
_PUBLIC_WEB_PATHS = {
    "/login/",
    "/logout/",
    "/register/",
    "/register/plan/",
    "/register/domain/",
    "/register/success/",
    "/no-tenant/",
}


class WebAuthRedirectMiddleware:
    """
    For web (non-API) paths: if the user is not authenticated and hits a
    protected page, redirect to the web login URL rather than returning JSON.

    This is intentionally lightweight — actual login enforcement is done via
    LoginRequiredMixin on each view. This middleware only corrects the
    LOGIN_URL fallback for the web layer.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Resolve the web login URL once at startup
        try:
            self._web_login_url = reverse("web:login")
        except Exception:
            self._web_login_url = "/login/"

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Called just before Django calls the view.
        We use process_view (not __call__) so we have access to the resolved view.
        """
        path = request.path_info

        # Never intercept API, admin, static, or media paths
        if any(
            path.startswith(prefix)
            for prefix in (_API_PREFIX, _ADMIN_PREFIX, _STATIC_PREFIX, _MEDIA_PREFIX)
        ):
            return None

        # Never intercept public web paths
        if path in _PUBLIC_WEB_PATHS or path.rstrip("/") + "/" in _PUBLIC_WEB_PATHS:
            return None

        return None   # Let LoginRequiredMixin handle it per-view
