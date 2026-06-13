# apps/web/audit/views.py
"""
Web views for the Audit module.

Superuser sees all colleges.
College Admin sees only their own college's audit logs.
"""
import logging
from django.shortcuts import render
from django.views import View

from apps.audit.models import AuditLog
from apps.web.mixins import CollegeAdminRequiredMixin, SuperUserRequiredMixin

logger = logging.getLogger(__name__)


class AuditLogListView(CollegeAdminRequiredMixin, View):
    template_name = "web/audit/list.html"
    PAGE_SIZE = 100

    def get(self, request):
        college = request.college
        qs = (
            AuditLog.objects.filter(college=college)
            .select_related("actor")
            .order_by("-created_at")
        )

        # Filters
        actor_q  = request.GET.get("actor", "").strip()
        action_q = request.GET.get("action", "").strip()
        entity_q = request.GET.get("entity", "").strip()

        if actor_q:
            qs = qs.filter(actor__email__icontains=actor_q)
        if action_q:
            qs = qs.filter(action__icontains=action_q)
        if entity_q:
            qs = qs.filter(entity_type__icontains=entity_q)

        total = qs.count()
        logs  = qs[:self.PAGE_SIZE]

        return render(request, self.template_name, {
            "page_title":   "Audit Log",
            "page_subtitle": f"{college.name} · Last {min(total, self.PAGE_SIZE)} entries",
            "logs":         logs,
            "total":        total,
            "actor_q":      actor_q,
            "action_q":     action_q,
            "entity_q":     entity_q,
        })


class PlatformAuditLogView(SuperUserRequiredMixin, View):
    """Platform-level audit — superuser sees all logs across all colleges."""
    template_name = "web/audit/platform_list.html"
    PAGE_SIZE = 200

    def get(self, request):
        qs = (
            AuditLog.objects.select_related("actor", "college")
            .order_by("-created_at")
        )
        college_q = request.GET.get("college", "").strip()
        actor_q   = request.GET.get("actor", "").strip()
        action_q  = request.GET.get("action", "").strip()

        if college_q:
            qs = qs.filter(college__name__icontains=college_q)
        if actor_q:
            qs = qs.filter(actor__email__icontains=actor_q)
        if action_q:
            qs = qs.filter(action__icontains=action_q)

        total = qs.count()
        logs  = qs[:self.PAGE_SIZE]

        return render(request, self.template_name, {
            "page_title":   "Platform Audit Log",
            "page_subtitle": f"All colleges · Last {min(total, self.PAGE_SIZE)} entries",
            "logs":         logs,
            "total":        total,
            "college_q":    college_q,
            "actor_q":      actor_q,
            "action_q":     action_q,
        })
