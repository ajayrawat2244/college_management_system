# apps/web/audit/urls.py
from django.urls import path
from apps.web.audit.views import AuditLogListView, PlatformAuditLogView

urlpatterns = [
    path("",          AuditLogListView.as_view(),     name="audit_log"),
    path("platform/", PlatformAuditLogView.as_view(), name="platform_audit_log"),
]
