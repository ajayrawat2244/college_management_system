# apps/web/utils.py
"""
Utility functions shared across all web sub-modules.
No views, no models — pure helpers.
"""
from django.urls import reverse

from apps.accounts.models import UserRole
from apps.platforms.permissions import (
    ROLE_COLLEGE_ADMIN,
    ROLE_STUDENT,
    ROLE_TEACHER,
)

# ── Role → dashboard URL map ─────────────────────────────────
_ROLE_DASHBOARD_MAP = {
    ROLE_COLLEGE_ADMIN: "web:admin_dashboard",
    ROLE_TEACHER:       "web:teacher_dashboard",
    ROLE_STUDENT:       "web:student_dashboard",
}
_PLATFORM_DASHBOARD = "web:platform_dashboard"
_FALLBACK_DASHBOARD  = "web:dashboard"


def get_post_login_redirect(user, college):
    """
    Return the absolute URL the user should land on after login.

    Resolution order:
      1. Platform superuser → platform admin dashboard.
      2. College-scoped user → role-specific dashboard.
      3. Fallback → generic dashboard shell.
    """
    if user.is_superuser:
        return reverse(_PLATFORM_DASHBOARD)

    if college:
        primary = (
            UserRole.objects
            .filter(user=user, college=college, status="active")
            .select_related("role")
            .order_by("-is_primary", "role__code")
            .first()
        )
        if primary:
            url_name = _ROLE_DASHBOARD_MAP.get(primary.role.code, _FALLBACK_DASHBOARD)
            return reverse(url_name)

    return reverse(_FALLBACK_DASHBOARD)


def get_user_primary_role_code(user, college):
    """
    Return the role code string for the current user in this college.
    Used by context processor for display / template gating.
    """
    if user.is_superuser:
        return "superuser"
    if not college:
        return None
    role_obj = (
        UserRole.objects
        .filter(user=user, college=college, status="active")
        .select_related("role")
        .order_by("-is_primary")
        .first()
    )
    return role_obj.role.code if role_obj else None


def get_user_profile(user, college):
    """
    Return the StudentProfile or TeacherProfile for the user if it exists.
    Returns (profile_type, profile_object) or (None, None).
    """
    role_code = get_user_primary_role_code(user, college)
    if role_code == ROLE_STUDENT:
        try:
            return "student", user.student_profile
        except Exception:
            return "student", None
    if role_code in (ROLE_TEACHER, ROLE_COLLEGE_ADMIN):
        try:
            return "teacher", user.teacher_profile
        except Exception:
            return "teacher", None
    return None, None


def trial_days_remaining(subscription):
    """Return integer days left in trial, or None if not on trial."""
    from django.utils import timezone as tz
    if not subscription or subscription.status != "trial":
        return None
    if not subscription.trial_ends_at:
        return None
    delta = subscription.trial_ends_at - tz.now()
    return max(0, delta.days)
