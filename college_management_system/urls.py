# college_management_system/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth
    path("api/auth/", include("apps.accounts.urls.auth")),

    # Apps
    path("api/platform/", include("apps.platforms.urls")),
    path("api/accounts/", include("apps.accounts.urls.accounts")),
    path("api/academics/", include("apps.academics.urls")),
    path("api/attendance/", include("apps.attendance.urls")),
    path("api/content/", include("apps.content.urls")),
    path("api/exams/", include("apps.exams.urls")),
    path("api/finance/", include("apps.finance.urls")),
    path("api/audit/", include("apps.audit.urls")),

    path("", include("apps.web.urls")),

]
