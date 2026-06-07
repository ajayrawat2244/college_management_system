from django.urls import path

from apps.web.views import DashboardView, StudentDetailView, StudentListView

app_name = "web"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("students/", StudentListView.as_view(), name="student-list"),
    path("students/<uuid:student_id>/", StudentDetailView.as_view(), name="student-detail"),
]
