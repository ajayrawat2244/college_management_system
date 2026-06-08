# apps/web/dashboard/urls.py
from django.urls import path

from apps.web.dashboard.views import DashboardView, NoTenantView

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("no-tenant/", NoTenantView.as_view(), name="no_tenant"),
]
