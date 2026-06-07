# apps/platforms/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.platforms.views import (
    CollegeSettingsView,
    CollegeSubscriptionViewSet,
    CollegeViewSet,
    FeatureViewSet,
    FileAssetViewSet,
    SubscriptionInvoiceViewSet,
    SubscriptionPaymentViewSet,
    SubscriptionPlanViewSet,
)

router = DefaultRouter()
router.register("colleges", CollegeViewSet, basename="college")
router.register("plans", SubscriptionPlanViewSet, basename="subscription-plan")
router.register("features", FeatureViewSet, basename="feature")
router.register("subscriptions", CollegeSubscriptionViewSet, basename="college-subscription")
router.register("invoices", SubscriptionInvoiceViewSet, basename="subscription-invoice")
router.register("payments", SubscriptionPaymentViewSet, basename="subscription-payment")
router.register("files", FileAssetViewSet, basename="file-asset")

urlpatterns = [
    path("", include(router.urls)),
    # Single-resource settings endpoint
    path("settings/", CollegeSettingsView.as_view({"get": "retrieve", "patch": "partial_update"})),
]
