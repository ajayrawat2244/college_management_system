# apps/audit/views.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.audit.models import AuditLog
from apps.audit.serializers import AuditLogSerializer
from apps.platforms.mixins import CollegeScopedMixin
from apps.platforms.permissions import IsCollegeAdmin, IsTenantResolved


class AuditLogViewSet(CollegeScopedMixin, ReadOnlyModelViewSet):
    """Read-only audit log — College Admin and above."""

    queryset = AuditLog.objects.select_related("actor", "college").order_by("-created_at")
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["entity_type", "actor"]
    search_fields = ["action", "entity_type", "actor__email"]
    ordering_fields = ["created_at"]
