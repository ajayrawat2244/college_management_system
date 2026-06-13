# apps/web/platform_admin/views.py
"""
Platform-level admin views — superuser only.
Manages all colleges on the platform.
"""
import logging

from django.contrib import messages
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.models import User
from apps.platforms.models import College, CollegeStatus, CollegeSubscription
from apps.web.mixins import SuperUserRequiredMixin

logger = logging.getLogger(__name__)


class PlatformDashboardView(SuperUserRequiredMixin, View):
    template_name = "web/platform_admin/dashboard.html"

    def get(self, request):
        colleges = (
            College.objects
            .prefetch_related(
                Prefetch(
                    "subscriptions",
                    queryset=CollegeSubscription.objects.select_related("plan")
                    .filter(status__in=["trial", "active", "past_due"])
                    .order_by("-created_at"),
                    to_attr="active_subs",
                )
            )
            .annotate(user_count=Count("users"))
            .order_by("name")
        )

        total_colleges = colleges.count()
        active_colleges = colleges.filter(status=CollegeStatus.ACTIVE).count()
        total_users = User.objects.filter(is_superuser=False).count()

        return render(request, self.template_name, {
            "page_title":       "Platform Admin",
            "page_subtitle":    "All Colleges",
            "colleges":         colleges,
            "total_colleges":   total_colleges,
            "active_colleges":  active_colleges,
            "total_users":      total_users,
        })


class CollegeDetailView(SuperUserRequiredMixin, View):
    template_name = "web/platform_admin/college_detail.html"

    def get(self, request, college_id):
        college = get_object_or_404(College, id=college_id)
        subscriptions = (
            CollegeSubscription.objects
            .filter(college=college)
            .select_related("plan")
            .order_by("-created_at")
        )
        users = (
            User.objects
            .filter(college=college)
            .prefetch_related("user_roles__role")
            .order_by("first_name")
        )
        return render(request, self.template_name, {
            "page_title":    college.name,
            "page_subtitle": "College Detail",
            "viewed_college": college,
            "subscriptions": subscriptions,
            "users":         users,
        })

    def post(self, request, college_id):
        """Toggle college active / suspended."""
        college = get_object_or_404(College, id=college_id)
        action  = request.POST.get("action")
        if action == "suspend":
            college.status = CollegeStatus.SUSPENDED
            messages.warning(request, f"{college.name} suspended.")
        elif action == "activate":
            college.status = CollegeStatus.ACTIVE
            messages.success(request, f"{college.name} reactivated.")
        college.save(update_fields=["status"])
        return redirect("web:platform_college_detail", college_id=college.id)
