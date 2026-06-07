# apps/platforms/permissions.py
"""
All custom DRF permission classes for the CMS.

Permission hierarchy:
    IsSuperUser          — platform-level; full access everywhere
    IsCollegeAdmin       — college-level; full access within their tenant
    IsTeacher            — within tenant; academic write access
    IsStudent            — within tenant; read-only personal/academic data
    IsTenantResolved     — guard: ensures request.college is set
    HasFeatureAccess     — checks subscription plan for a named feature_code
"""

from rest_framework.permissions import BasePermission

from apps.platforms.services.subscription import SubscriptionService


# ---------------------------------------------------------------------------
# Role code constants — must match Role.code values in the DB
# ---------------------------------------------------------------------------
ROLE_SUPERUSER = "superuser"
ROLE_COLLEGE_ADMIN = "college_admin"
ROLE_TEACHER = "teacher"
ROLE_STUDENT = "student"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_role(user, college, *role_codes):
    """Return True if the user has any of the given roles for this college."""
    if not user or not user.is_authenticated:
        return False
    # SuperUsers carry a platform-scoped role (college=None)
    return user.user_roles.filter(
        role__code__in=role_codes,
        status="active",
    ).filter(
        # Either matches the college exactly, or is a platform-wide role
        college=college
    ).exists() or user.user_roles.filter(
        role__code__in=role_codes,
        status="active",
        college__isnull=True,
    ).exists()


# ---------------------------------------------------------------------------
# Core permissions
# ---------------------------------------------------------------------------

class IsTenantResolved(BasePermission):
    """Requires that TenantResolutionMiddleware found a valid college."""

    message = "College tenant could not be resolved. Provide X-College-ID header."

    def has_permission(self, request, view):
        return bool(request.college)


class IsSuperUser(BasePermission):
    """Only platform-level SuperUsers (is_superuser=True) pass."""

    message = "Only SuperUsers can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class IsCollegeAdmin(BasePermission):
    """User must have the college_admin role within the resolved college."""

    message = "Only College Admins can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if not request.college:
            return False
        return _has_role(request.user, request.college, ROLE_COLLEGE_ADMIN)


class IsTeacher(BasePermission):
    """User must have teacher role within the resolved college."""

    message = "Only Teachers can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if not request.college:
            return False
        return _has_role(
            request.user, request.college, ROLE_COLLEGE_ADMIN, ROLE_TEACHER
        )


class IsStudent(BasePermission):
    """User must have student role within the resolved college."""

    message = "Only Students can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not request.college:
            return False
        return _has_role(
            request.user,
            request.college,
            ROLE_SUPERUSER,
            ROLE_COLLEGE_ADMIN,
            ROLE_TEACHER,
            ROLE_STUDENT,
        )


class IsCollegeAdminOrTeacher(BasePermission):
    """College Admin or Teacher within the resolved college."""

    message = "Only College Admins or Teachers can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if not request.college:
            return False
        return _has_role(
            request.user, request.college, ROLE_COLLEGE_ADMIN, ROLE_TEACHER
        )


# ---------------------------------------------------------------------------
# Subscription / Feature gating
# ---------------------------------------------------------------------------

class HasFeatureAccess(BasePermission):
    """
    Gate a view behind a subscription feature.

    Usage on a ViewSet::

        permission_classes = [IsAuthenticated, IsTenantResolved, HasFeatureAccess]
        required_feature = "exam_results"   # must match Feature.feature_code

    The check delegates to SubscriptionService which reads the college's active
    plan entitlements (with a short cache) and checks feature_overrides in
    CollegeSettings.
    """

    message = "Your subscription plan does not include access to this feature."

    def has_permission(self, request, view):
        if not request.college:
            return False
        feature_code = getattr(view, "required_feature", None)
        if not feature_code:
            return True   # No feature gate specified on the view
        return SubscriptionService.college_has_feature(request.college, feature_code)
