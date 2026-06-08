# apps/web/urls.py
"""
Top-level URL configuration for the web layer (apps.web).

Included in the project's root URLconf under the 'web' namespace.

URL layout:
  /               → RootRedirectView (→ login or dashboard)
  /login/         → LoginView
  /logout/        → LogoutView
  /change-password/ → ChangePasswordView
  /dashboard/     → DashboardView
  /no-tenant/     → NoTenantView
  /register/      → Onboarding Step 1
  /register/plan/ → Onboarding Step 2
  /register/domain/ → Onboarding Step 3
  /platform/      → Platform admin (superuser only)
"""
from django.urls import include, path

from apps.web.dashboard.views import RootRedirectView

app_name = "web"

urlpatterns = [
    # Root
    path("", RootRedirectView.as_view(), name="root"),

    # Auth
    path("", include("apps.web.auth.urls")),

    # Dashboard + error pages
    path("dashboard/", include("apps.web.dashboard.urls")),

    # Public onboarding wizard
    path("register/", include("apps.web.onboarding.urls")),

    # Platform superuser area
    path("platform/", include("apps.web.platform_admin.urls")),
]
