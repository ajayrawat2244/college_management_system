# apps/web/context_processors.py
"""
Context processors injected into every template rendered by the web layer.

Registered in settings.py under TEMPLATES[0]['OPTIONS']['context_processors'].
"""
from apps.platforms.services.subscription import SubscriptionService
from apps.web.utils import get_user_primary_role_code


def tenant(request):
    """
    Injects the resolved college tenant as ``college`` and ``tenant``
    (both point to the same object; ``tenant`` is the legacy name used in
    the existing sidebar/topbar partials).
    """
    college = getattr(request, "college", None)
    return {
        "college": college,
        "tenant": college,          # alias — existing templates use {{ tenant.name }}
    }


def user_role(request):
    """
    Injects the current user's primary role code as ``user_role_code`` so
    templates can show/hide nav items without a DB query per template tag.
    """
    if not request.user.is_authenticated:
        return {"user_role_code": None}
    college = getattr(request, "college", None)
    return {
        "user_role_code": get_user_primary_role_code(request.user, college),
    }


def subscription(request):
    """
    Injects basic subscription state so templates can gate feature links.

    Keys injected:
      ``subscription``         — CollegeSubscription object or None
      ``subscription_status``  — status string or None
    """
    college = getattr(request, "college", None)
    if not college:
        return {"subscription": None, "subscription_status": None}
    sub = SubscriptionService.get_active_subscription(college)
    return {
        "subscription": sub,
        "subscription_status": sub.status if sub else None,
    }
