# apps/web/context_processors.py
"""
Context processors injected into every template in the web layer.

Registered in settings.py → TEMPLATES[0]['OPTIONS']['context_processors'].
"""
from apps.platforms.services.subscription import SubscriptionService
from apps.web.utils import get_user_primary_role_code, trial_days_remaining


def tenant(request):
    """Inject resolved college as both ``college`` and ``tenant``."""
    college = getattr(request, "college", None)
    return {
        "college": college,
        "tenant":  college,      # alias — some existing partials use {{ tenant.name }}
    }


def user_role(request):
    """Inject the user's primary role code as ``user_role_code``."""
    if not request.user.is_authenticated:
        return {"user_role_code": None}
    college = getattr(request, "college", None)
    return {
        "user_role_code": get_user_primary_role_code(request.user, college),
    }


def subscription(request):
    """
    Inject subscription state:
      ``subscription``         — CollegeSubscription or None
      ``subscription_status``  — status string or None
      ``trial_days``           — integer days remaining in trial, or None
      ``entitlements``         — dict of feature_code → {is_enabled, limit_value}
    """
    college = getattr(request, "college", None)
    if not college:
        return {
            "subscription": None,
            "subscription_status": None,
            "trial_days": None,
            "entitlements": {},
        }

    sub = SubscriptionService.get_active_subscription(college)
    entitlements = SubscriptionService.get_entitlements(college) if sub else {}

    return {
        "subscription": sub,
        "subscription_status": sub.status if sub else None,
        "trial_days": trial_days_remaining(sub),
        "entitlements": entitlements,
    }
