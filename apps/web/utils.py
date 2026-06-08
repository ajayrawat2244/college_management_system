# apps/web/utils.py
"""
Utility functions shared across all web sub-modules.
"""
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.platforms.permissions import (
    ROLE_COLLEGE_ADMIN,
    ROLE_STUDENT,
    ROLE_TEACHER,
)

# Role code → dashboard URL name mapping
_ROLE_DASHBOARD_MAP = {
    ROLE_COLLEGE_ADMIN: "web:dashboard",
    ROLE_TEACHER: "web:dashboard",       # same shell, different nav items shown
    ROLE_STUDENT: "web:dashboard",
}

_PLATFORM_ADMIN_DASHBOARD = "web:platform_dashboard"


def get_post_login_redirect(user, college):
    """
    Return the URL the user should land on after a successful login.

    Resolution order:
      1. Platform superuser → platform admin dashboard (no college needed).
      2. College-scoped user → college dashboard (tenant must be resolved).
      3. Fallback → root (handles edge cases gracefully).
    """
    if user.is_superuser:
        return reverse(_PLATFORM_ADMIN_DASHBOARD)

    if college:
        # Pick the highest-priority role for this college
        primary_role = (
            UserRole.objects.filter(
                user=user,
                college=college,
                status="active",
            )
            .select_related("role")
            .order_by("-is_primary", "role__code")
            .first()
        )
        if primary_role:
            url_name = _ROLE_DASHBOARD_MAP.get(
                primary_role.role.code, "web:dashboard"
            )
            return reverse(url_name)

    return "/"


def get_user_primary_role_code(user, college):
    """
    Return the role code string for display purposes (e.g. in the topbar).
    Returns None if no role is found.
    """
    if user.is_superuser:
        return "superuser"
    if not college:
        return None
    role_obj = (
        UserRole.objects.filter(user=user, college=college, status="active")
        .select_related("role")
        .order_by("-is_primary")
        .first()
    )
    return role_obj.role.code if role_obj else None
