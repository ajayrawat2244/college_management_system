from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.platforms.models import College, CollegeStatus
from apps.web.services.dashboard import get_dashboard_context
from apps.web.services.students import (
    build_student_filters,
    build_student_queryset,
    get_student_detail_context,
    paginate_students,
)


class CollegeContextMixin(LoginRequiredMixin):
    login_url = "/admin/login/"

    def get_college(self):
        college = getattr(self.request, "college", None)
        if college is not None:
            return college

        user_college = getattr(self.request.user, "college", None)
        if user_college is not None:
            return user_college

        if self.request.user.is_superuser:
            college = College.objects.filter(status=CollegeStatus.ACTIVE).order_by("name").first()
            if college is not None:
                return college

        raise PermissionDenied(
            "College tenant could not be resolved. "
            "Please use a valid tenant/subdomain or assign a college to this account."
        )

    def add_common_context(self, context=None):
        context = context or {}
        context["college"] = self.get_college()
        context["current_user"] = self.request.user
        return context


class DashboardView(CollegeContextMixin, TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        college = self.get_college()
        context = super().get_context_data(**kwargs)
        context.update(get_dashboard_context(college))
        context["college"] = college
        return context


class StudentListView(CollegeContextMixin, View):
    template_name = "students/list.html"
    per_page = 12

    def get(self, request, *args, **kwargs):
        college = self.get_college()
        queryset = build_student_queryset(college, request.GET)
        page_obj = paginate_students(queryset, request.GET.get("page"), self.per_page)
        context = self.add_common_context(
            {
                "students": page_obj.object_list,
                "page_obj": page_obj,
                "paginator": page_obj.paginator,
                "is_paginated": page_obj.has_other_pages(),
                "search": request.GET.get("search", ""),
                "status": request.GET.get("status", ""),
                "program": request.GET.get("program", ""),
                "section": request.GET.get("section", ""),
                "batch": request.GET.get("batch", ""),
            }
        )
        context.update(build_student_filters(college))
        return render(request, self.template_name, context)


class StudentDetailView(CollegeContextMixin, View):
    template_name = "students/detail.html"

    def get(self, request, student_id, *args, **kwargs):
        college = self.get_college()
        context = self.add_common_context(get_student_detail_context(college, student_id))
        return render(request, self.template_name, context)
