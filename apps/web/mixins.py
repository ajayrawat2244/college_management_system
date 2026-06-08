# apps/web/mixins.py
"""
Shared view mixins for the web layer.

These are Django class-based view mixins — NOT DRF mixins.
They mirror the DRF CollegeScopedMixin / permission pattern
but work with Django's LoginRequiredMixin / View pattern.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from apps.platforms.permissions import (
    ROLE_COLLEGE_ADMIN,
    ROLE_STUDENT,
    ROLE_TEACHER,
    _has_role,
)


class TenantRequiredMixin:
    """
    Ensures request.college is resolved before proceeding.
    On failure: renders a friendly 'no tenant' error page instead of a
    JSON 403 (which the DRF permission would produce).

    Place AFTER LoginRequiredMixin in MRO so the user is authenticated first.
    """

    def dispatch(self, request, *args, **kwargs):
        if not getattr(request, "college", None):
            return redirect("web:no_tenant")
        return super().dispatch(request, *args, **kwargs)


class CollegeAdminRequiredMixin(LoginRequiredMixin, TenantRequiredMixin):
    """
    Gate: user must be authenticated + tenant resolved + have college_admin role
    (or be a platform superuser).
    """

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        # super() already checked login + tenant; now check role
        if not request.user.is_authenticated:
            return response  # LoginRequiredMixin already redirects
        if request.user.is_superuser:
            return response
        if not _has_role(request.user, request.college, ROLE_COLLEGE_ADMIN):
            raise PermissionDenied("You do not have college admin access.")
        return response


class TeacherRequiredMixin(LoginRequiredMixin, TenantRequiredMixin):
    """Gate: college_admin or teacher within the resolved college."""

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return response
        if request.user.is_superuser:
            return response
        if not _has_role(
            request.user, request.college, ROLE_COLLEGE_ADMIN, ROLE_TEACHER
        ):
            raise PermissionDenied("You do not have teacher access.")
        return response


class StudentRequiredMixin(LoginRequiredMixin, TenantRequiredMixin):
    """Gate: any authenticated role within the resolved college."""

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return response
        if request.user.is_superuser:
            return response
        if not _has_role(
            request.user,
            request.college,
            ROLE_COLLEGE_ADMIN,
            ROLE_TEACHER,
            ROLE_STUDENT,
        ):
            raise PermissionDenied("You do not have access to this college.")
        return response


class SuperUserRequiredMixin(LoginRequiredMixin):
    """Gate: platform-level superuser only (no tenant needed)."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_superuser:
            raise PermissionDenied("Only platform superusers can access this area.")
        return super().dispatch(request, *args, **kwargs)
