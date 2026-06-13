# apps/web/dashboard/urls.py
from django.urls import path
from apps.web.dashboard.views import (
    AdminDashboardView,
    DashboardView,
    ForbiddenView,
    NoTenantView,
    StudentDashboardView,
    SubscriptionRequiredView,
    TeacherDashboardView,
)

urlpatterns = [
    path("",                      DashboardView.as_view(),             name="dashboard"),
    path("admin/",                AdminDashboardView.as_view(),        name="admin_dashboard"),
    path("teacher/",              TeacherDashboardView.as_view(),      name="teacher_dashboard"),
    path("student/",              StudentDashboardView.as_view(),      name="student_dashboard"),
    path("no-tenant/",            NoTenantView.as_view(),              name="no_tenant"),
    path("subscription-required/", SubscriptionRequiredView.as_view(), name="subscription_required"),
    path("forbidden/",            ForbiddenView.as_view(),             name="forbidden"),
]
