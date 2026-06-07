# apps/platforms/views.py
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.platforms.mixins import CollegeScopedMixin
from apps.platforms.models import (
    College,
    CollegeSettings,
    CollegeSubscription,
    Feature,
    FileAsset,
    SubscriptionInvoice,
    SubscriptionPayment,
    SubscriptionPlan,
)
from apps.platforms.permissions import IsCollegeAdmin, IsSuperUser, IsTenantResolved
from apps.platforms.serializers import (
    CollegeSerializer,
    CollegeSettingsSerializer,
    CollegeSubscriptionSerializer,
    FeatureSerializer,
    FileAssetSerializer,
    SubscriptionInvoiceSerializer,
    SubscriptionPaymentSerializer,
    SubscriptionPlanSerializer,
)
from apps.platforms.services.subscription import SubscriptionService


# ---------------------------------------------------------------------------
# SuperUser-only: College management
# ---------------------------------------------------------------------------

class CollegeViewSet(ModelViewSet):
    """CRUD for colleges — SuperUser only."""

    queryset = College.objects.all().order_by("name")
    serializer_class = CollegeSerializer
    permission_classes = [IsAuthenticated, IsSuperUser]
    search_fields = ["name", "code", "subdomain"]
    filterset_fields = ["status"]
    ordering_fields = ["name", "created_at"]


class SubscriptionPlanViewSet(ModelViewSet):
    """Manage subscription plans — SuperUser only."""

    queryset = SubscriptionPlan.objects.prefetch_related("plan_features__feature").all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated, IsSuperUser]
    filterset_fields = ["is_active", "billing_cycle"]


class FeatureViewSet(ReadOnlyModelViewSet):
    """Read-only catalog of features. SuperUser can also write."""

    queryset = Feature.objects.all().order_by("module_name", "name")
    serializer_class = FeatureSerializer
    permission_classes = [IsAuthenticated, IsSuperUser]
    filterset_fields = ["module_name", "is_active"]


# ---------------------------------------------------------------------------
# College Admin: Subscription & Settings within their tenant
# ---------------------------------------------------------------------------

class CollegeSubscriptionViewSet(CollegeScopedMixin, ModelViewSet):
    """View and manage the college's subscription."""

    queryset = CollegeSubscription.objects.select_related("plan").all()
    serializer_class = CollegeSubscriptionSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["status"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    @action(detail=False, methods=["get"])
    def entitlements(self, request):
        """Return current feature entitlements for the college."""
        college = self.get_college()
        data = SubscriptionService.get_entitlements(college)
        return Response(data)


class SubscriptionInvoiceViewSet(CollegeScopedMixin, ReadOnlyModelViewSet):
    """Read-only list of subscription invoices."""

    queryset = SubscriptionInvoice.objects.all().order_by("-invoice_date")
    serializer_class = SubscriptionInvoiceSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["status"]


class SubscriptionPaymentViewSet(CollegeScopedMixin, ReadOnlyModelViewSet):
    """Read-only list of subscription payments."""

    queryset = SubscriptionPayment.objects.all().order_by("-paid_at")
    serializer_class = SubscriptionPaymentSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]


class CollegeSettingsView(CollegeScopedMixin, ModelViewSet):
    """
    Single-object settings for the college.
    GET  /api/platform/settings/  → retrieve
    PATCH /api/platform/settings/ → partial update
    """

    queryset = CollegeSettings.objects.all()
    serializer_class = CollegeSettingsSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        college = self.get_college()
        obj, _ = CollegeSettings.objects.get_or_create(college=college)
        self.check_object_permissions(self.request, obj)
        return obj


# ---------------------------------------------------------------------------
# File Upload (all authenticated college members)
# ---------------------------------------------------------------------------

class FileAssetViewSet(CollegeScopedMixin, ModelViewSet):
    """Upload and retrieve file assets."""

    queryset = FileAsset.objects.all().order_by("-created_at")
    serializer_class = FileAssetSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved]
    parser_classes = [MultiPartParser]
    filterset_fields = ["asset_kind", "storage_backend"]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def perform_create(self, serializer):
        serializer.save(
            college=self.get_college(),
            uploaded_by=self.request.user,
        )
