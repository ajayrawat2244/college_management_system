# apps/web/auth/views.py
"""
Session-based login / logout views for the server-rendered web layer.

These are pure Django views (not DRF). They work with the existing
TenantResolutionMiddleware: the middleware has already set request.college
from the subdomain before this view is called.

Login flow:
  1. User visits  college.cms.localhost/login/
  2. TenantResolutionMiddleware resolves request.college = College(...)
  3. LoginView validates credentials against the resolved college's user pool.
  4. On success → redirect to role-appropriate dashboard.
  5. On failure → re-render form with error.

Platform superusers (is_superuser=True) may log in from any subdomain or
from the bare domain (request.college = None) and are redirected to the
platform admin area.
"""
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views import View
from django.utils.decorators import method_decorator

from apps.web.auth.forms import WebChangePasswordForm, WebLoginForm
from apps.web.utils import get_post_login_redirect

logger = logging.getLogger(__name__)


class LoginView(View):
    """GET /login/ — render form.  POST /login/ — authenticate & redirect."""

    template_name = "web/auth/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(get_post_login_redirect(request.user, getattr(request, "college", None)))
        form = WebLoginForm()
        return render(request, self.template_name, self._ctx(request, form))

    def post(self, request):
        form = WebLoginForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._ctx(request, form))

        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]

        user = authenticate(request, username=email, password=password)

        if user is None:
            form.add_error(None, "Invalid email or password.")
            return render(request, self.template_name, self._ctx(request, form))

        if not user.is_active or user.status in ("blocked", "inactive", "archived"):
            form.add_error(None, "Your account is inactive or blocked. Contact your administrator.")
            return render(request, self.template_name, self._ctx(request, form))

        college = getattr(request, "college", None)

        # Non-superusers must belong to the resolved college tenant
        if not user.is_superuser and college and user.college_id != college.id:
            form.add_error(None, "Your account does not belong to this college.")
            logger.warning(
                "Login attempt: user %s does not belong to college %s",
                email,
                college.code,
            )
            return render(request, self.template_name, self._ctx(request, form))

        login(request, user)
        logger.info("Web login: %s → college=%s", email, college)

        redirect_url = get_post_login_redirect(user, college)
        return redirect(redirect_url)

    @staticmethod
    def _ctx(request, form):
        college = getattr(request, "college", None)
        return {
            "form": form,
            "college": college,
            "college_name": college.name if college else "Student Management System",
        }


class LogoutView(View):
    """POST /logout/ — end session and redirect to login."""

    def post(self, request):
        logout(request)
        messages.success(request, "You have been signed out.")
        return redirect("web:login")

    # Allow GET logout during development (convenience)
    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
        return redirect("web:login")


@method_decorator(login_required(login_url="web:login"), name="dispatch")
class ChangePasswordView(View):
    template_name = "web/auth/change_password.html"

    def get(self, request):
        return render(request, self.template_name, {"form": WebChangePasswordForm()})

    def post(self, request):
        form = WebChangePasswordForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        user = request.user
        if not user.check_password(form.cleaned_data["old_password"]):
            form.add_error("old_password", "Current password is incorrect.")
            return render(request, self.template_name, {"form": form})

        user.set_password(form.cleaned_data["new_password"])
        user.save(update_fields=["password"])
        # Re-authenticate so session stays valid
        login(request, user)
        messages.success(request, "Password changed successfully.")
        return redirect("web:dashboard")
