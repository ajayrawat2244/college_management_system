# apps/web/dashboard/views.py
"""
Dashboard shell view.

This pass renders a working dashboard frame with real tenant context.
KPI data is stubbed with safe fallbacks — individual module pages
(students, fees, attendance, etc.) will populate real querysets in
later passes.
"""
import logging

from django.views import View
from django.shortcuts import render, redirect

from apps.web.mixins import LoginRequiredMixin, TenantRequiredMixin

logger = logging.getLogger(__name__)


class DashboardView(LoginRequiredMixin, TenantRequiredMixin, View):
    """
    Main dashboard shell. Accessible to any authenticated user with a
    resolved tenant (college_admin, teacher, student all land here;
    role-specific widgets are toggled via template tags).
    """

    login_url = "web:login"
    template_name = "web/dashboard/dashboard.html"

    def get(self, request):
        college = request.college

        # --- Stub context: replaced by real aggregations in later passes ---
        ctx = {
            "page_title": "Dashboard",
            "page_subtitle": f"{college.name} · Overview",
            # KPI stubs — will be wired to real querysets in later passes
            "total_admissions": "—",
            "total_enquiries": "—",
            "total_revenue": "—",
            "revenue_target": "—",
            "active_courses": "—",
            "launching_soon": "—",
            "pending_enquiries": "—",
        }
        return render(request, self.template_name, ctx)


class RootRedirectView(View):
    """
    GET / — redirect unauthenticated users to login, authenticated to dashboard.
    """

    def get(self, request):
        if request.user.is_authenticated:
            from apps.web.utils import get_post_login_redirect
            return redirect(get_post_login_redirect(request.user, getattr(request, "college", None)))
        return redirect("web:login")


class NoTenantView(View):
    """Friendly error when the subdomain doesn't map to any college."""

    template_name = "web/errors/no_tenant.html"

    def get(self, request):
        return render(request, self.template_name, status=404)
