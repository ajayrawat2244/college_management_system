# apps/web/platform_admin/urls.py
from django.urls import path
from apps.web.platform_admin.views import CollegeDetailView, PlatformDashboardView

urlpatterns = [
    path("",                            PlatformDashboardView.as_view(), name="platform_dashboard"),
    path("colleges/<uuid:college_id>/", CollegeDetailView.as_view(),     name="platform_college_detail"),
]
