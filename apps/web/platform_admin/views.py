# apps/web/platform_admin/views.py
"""
Platform-level admin views — superuser only.
This pass provides the shell; full CRUD pages come in a later pass.
"""
from django.shortcuts import render
from django.views import View

from apps.platforms.models import College
from apps.web.mixins import SuperUserRequiredMixin


class PlatformDashboardView(SuperUserRequiredMixin, View):
    """
    Superuser home — shows a list of all colleges on the platform.
    Tenant is NOT required (superusers operate at the platform level).
    """

    login_url = "web:login"
    template_name = "web/platform_admin/dashboard.html"

    def get(self, request):
        colleges = (
            College.objects.select_related()
            .prefetch_related("subscriptions")
            .order_by("name")
        )
        return render(request, self.template_name, {
            "colleges": colleges,
            "page_title": "Platform Admin",
            "page_subtitle": "All colleges on this platform",
        })
