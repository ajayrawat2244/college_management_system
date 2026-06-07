# apps/platforms/services/subscription.py
"""
SubscriptionService
-------------------
Single entry point for all subscription / feature-gate checks.

Flow:
  1. Find the college's active CollegeSubscription.
  2. Load PlanFeatures for that plan (whether a feature_code is enabled,
     and what its limit_value is).
  3. Merge with CollegeSettings.feature_overrides (college-level overrides
     take precedence over plan defaults).
  4. Return the result to the caller.

Results are NOT cached here (no Redis dependency yet); add Django's
cache framework call around get_entitlements() when you introduce caching.
"""

import logging

from apps.platforms.models import CollegeSubscription, CollegeSettings, SubscriptionStatus

logger = logging.getLogger(__name__)


class SubscriptionService:

    @staticmethod
    def get_active_subscription(college):
        """Return the active/trial CollegeSubscription or None."""
        return (
            CollegeSubscription.objects.select_related("plan")
            .filter(
                college=college,
                status__in=[
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.TRIAL,
                    SubscriptionStatus.PAST_DUE,
                ],
            )
            .order_by("-created_at")
            .first()
        )

    @staticmethod
    def get_entitlements(college):
        """
        Return a dict mapping feature_code -> {is_enabled, limit_value}.

        Merges plan-level PlanFeature rows with CollegeSettings.feature_overrides.
        feature_overrides format (stored in JSONB):
            {
                "exam_results": {"is_enabled": true, "limit_value": null},
                "bulk_sms":     {"is_enabled": false}
            }
        """
        subscription = SubscriptionService.get_active_subscription(college)
        if not subscription:
            return {}

        # Build base entitlements from plan
        entitlements = {}
        for pf in subscription.plan.plan_features.select_related("feature").all():
            entitlements[pf.feature.feature_code] = {
                "is_enabled": pf.is_enabled,
                "limit_value": pf.limit_value,
            }

        # Apply college-level overrides
        try:
            overrides = CollegeSettings.objects.get(college=college).feature_overrides
        except CollegeSettings.DoesNotExist:
            overrides = {}

        for feature_code, override in overrides.items():
            if feature_code in entitlements:
                entitlements[feature_code].update(override)
            else:
                entitlements[feature_code] = override

        return entitlements

    @staticmethod
    def college_has_feature(college, feature_code):
        """
        Returns True if the college's active subscription includes the feature
        and it is enabled (plan default + overrides considered).
        """
        entitlements = SubscriptionService.get_entitlements(college)
        feature = entitlements.get(feature_code)
        if not feature:
            return False
        return bool(feature.get("is_enabled", False))

    @staticmethod
    def get_feature_limit(college, feature_code):
        """
        Returns the limit_value for a feature, or None if unlimited / not found.
        """
        entitlements = SubscriptionService.get_entitlements(college)
        feature = entitlements.get(feature_code)
        if not feature:
            return None
        return feature.get("limit_value")
