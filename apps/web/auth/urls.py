# apps/web/auth/urls.py
from django.urls import path

from apps.web.auth.views import ChangePasswordView, LoginView, LogoutView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
]
