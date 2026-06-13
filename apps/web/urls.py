# apps/web/urls.py
from django.urls import include, path
from apps.web.dashboard.views import RootRedirectView

app_name = "web"

urlpatterns = [
    path("", RootRedirectView.as_view(), name="root"),
    path("", include("apps.web.auth.urls")),
    path("dashboard/",  include("apps.web.dashboard.urls")),
    path("college/",    include("apps.web.college_admin.urls")),
    path("register/",   include("apps.web.onboarding.urls")),
    path("platform/",   include("apps.web.platform_admin.urls")),
    path("academics/",  include("apps.web.academics.urls")),
    path("attendance/", include("apps.web.attendance.urls")),
    path("content/",    include("apps.web.content.urls")),
    path("exams/",      include("apps.web.exams.urls")),
    path("finance/",    include("apps.web.finance.urls")),
    path("audit/",      include("apps.web.audit.urls")),
]
