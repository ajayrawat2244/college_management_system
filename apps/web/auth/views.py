# apps/web/auth/views.py
"""
Session-based login / logout for the web layer.

Flow:
  1. TenantResolutionMiddleware runs → request.college set from subdomain
  2. LoginView authenticates user
  3. get_post_login_redirect() picks role-appropriate dashboard
  4. Superusers may log in from any subdomain (college = None is fine)
"""
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from apps.web.auth.forms import WebChangePasswordForm, WebLoginForm
from apps.web.utils import get_post_login_redirect

logger = logging.getLogger(__name__)


class LoginView(View):
    template_name = "web/auth/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(
                get_post_login_redirect(request.user, getattr(request, "college", None))
            )
        return render(request, self.template_name, self._ctx(request, WebLoginForm()))

    def post(self, request):
        form = WebLoginForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._ctx(request, form))

        email    = form.cleaned_data["email"]
        password = form.cleaned_data["password"]
        user     = authenticate(request, username=email, password=password)

        if user is None:
            form.add_error(None, "Invalid email or password.")
            return render(request, self.template_name, self._ctx(request, form))

        if not user.is_active or getattr(user, "status", "active") in ("blocked", "inactive", "archived"):
            form.add_error(None, "Your account is inactive. Contact your administrator.")
            return render(request, self.template_name, self._ctx(request, form))

        college = getattr(request, "college", None)

        # Non-superusers must belong to the resolved college
        if not user.is_superuser and college:
            if user.college_id != college.id:
                form.add_error(None, "Your account does not belong to this college.")
                logger.warning("Web login tenant mismatch: user=%s college=%s", email, college.code)
                return render(request, self.template_name, self._ctx(request, form))

        login(request, user)
        logger.info("Web login: user=%s college=%s", email, college)
        return redirect(get_post_login_redirect(user, college))

    @staticmethod
    def _ctx(request, form):
        college = getattr(request, "college", None)
        return {
            "form": form,
            "college": college,
            "college_name": college.name if college else "Student Management System",
        }


class LogoutView(View):
    def post(self, request):
        logout(request)
        messages.success(request, "You have been signed out.")
        return redirect("web:login")

    def get(self, request):
        # Allow GET for dev convenience
        logout(request)
        return redirect("web:login")


class ChangePasswordView(LoginRequiredMixin, View):
    login_url = "web:login"
    template_name = "web/auth/change_password.html"

    def get(self, request):
        return render(request, self.template_name, {"form": WebChangePasswordForm()})

    def post(self, request):
        form = WebChangePasswordForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        if not request.user.check_password(form.cleaned_data["old_password"]):
            form.add_error("old_password", "Current password is incorrect.")
            return render(request, self.template_name, {"form": form})

        request.user.set_password(form.cleaned_data["new_password"])
        request.user.save(update_fields=["password"])
        login(request, request.user)   # refresh session after password change
        messages.success(request, "Password changed successfully.")
        return redirect("web:dashboard")
