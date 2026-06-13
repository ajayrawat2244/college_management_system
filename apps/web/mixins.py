# apps/web/mixins.py
"""
Shared view mixins for the web layer (Django CBV — not DRF).

MRO for combined mixins:
    CollegeAdminRequiredMixin → LoginRequiredMixin → TenantRequiredMixin → View
    dispatch() is called left-to-right; each super() call cascades.
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
    Redirects to web:no_tenant (not JSON 403) when tenant is missing.
    Must appear AFTER LoginRequiredMixin in class declaration so the
    user is authenticated before we check the tenant.
    """

    def dispatch(self, request, *args, **kwargs):
        if not getattr(request, "college", None):
            return redirect("web:no_tenant")
        return super().dispatch(request, *args, **kwargs)


class CollegeAdminRequiredMixin(LoginRequiredMixin, TenantRequiredMixin):
    """Requires: authenticated + tenant resolved + college_admin role (or superuser)."""

    login_url = "web:login"

    def dispatch(self, request, *args, **kwargs):
        # LoginRequiredMixin.dispatch will redirect if not authenticated
        response = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return response
        if request.user.is_superuser:
            return response
        if not _has_role(request.user, request.college, ROLE_COLLEGE_ADMIN):
            raise PermissionDenied("You need college admin access for this page.")
        return response


class TeacherRequiredMixin(LoginRequiredMixin, TenantRequiredMixin):
    """Requires: authenticated + tenant + college_admin or teacher role."""

    login_url = "web:login"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return response
        if request.user.is_superuser:
            return response
        if not _has_role(request.user, request.college, ROLE_COLLEGE_ADMIN, ROLE_TEACHER):
            raise PermissionDenied("You need teacher or admin access for this page.")
        return response


class StudentRequiredMixin(LoginRequiredMixin, TenantRequiredMixin):
    """Requires: authenticated + tenant + any role within the college."""

    login_url = "web:login"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return response
        if request.user.is_superuser:
            return response
        if not _has_role(
            request.user, request.college,
            ROLE_COLLEGE_ADMIN, ROLE_TEACHER, ROLE_STUDENT,
        ):
            raise PermissionDenied("You do not have access to this college portal.")
        return response


class SuperUserRequiredMixin(LoginRequiredMixin):
    """Requires: authenticated + is_superuser (platform level — no tenant needed)."""

    login_url = "web:login"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_superuser:
            raise PermissionDenied("Only platform superusers can access this area.")
        return super().dispatch(request, *args, **kwargs)


class SubscriptionFeatureMixin:
    """
    Checks that the resolved college's active subscription includes
    ``required_feature``.  Set this attribute on the view class.

    Example:
        class ExamResultsView(CollegeAdminRequiredMixin, SubscriptionFeatureMixin, View):
            required_feature = "exam_results"
    """

    required_feature = None

    def dispatch(self, request, *args, **kwargs):
        if self.required_feature:
            from apps.platforms.services.subscription import SubscriptionService
            college = getattr(request, "college", None)
            if college and not SubscriptionService.college_has_feature(college, self.required_feature):
                return redirect("web:subscription_required")
        return super().dispatch(request, *args, **kwargs)
