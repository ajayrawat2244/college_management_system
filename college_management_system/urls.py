# college_management_system/urls.py
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # ── DRF API layer ────────────────────────────────────
    path("api/auth/",       include("apps.accounts.urls.auth")),
    path("api/platform/",   include("apps.platforms.urls")),
    path("api/accounts/",   include("apps.accounts.urls.accounts")),
    path("api/academics/",  include("apps.academics.urls")),
    path("api/attendance/", include("apps.attendance.urls")),
    path("api/content/",    include("apps.content.urls")),
    path("api/exams/",      include("apps.exams.urls")),
    path("api/finance/",    include("apps.finance.urls")),
    path("api/audit/",      include("apps.audit.urls")),

    # ── Web layer (server-rendered) ──────────────────────
    path("", include("apps.web.urls", namespace="web")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler403 = "apps.web.error_handlers.handler403"
handler404 = "apps.web.error_handlers.handler404"
handler500 = "apps.web.error_handlers.handler500"
