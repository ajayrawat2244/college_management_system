# apps/web/college_admin/views.py
"""
College Admin management views.

Covers:
  • College profile settings
  • User list + invite new user
  • Subscription status page
"""
import logging

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.accounts.models import Role, User, UserRole, UserStatus
from apps.platforms.models import CollegeSettings, CollegeSubscription
from apps.platforms.services.subscription import SubscriptionService
from apps.web.college_admin.forms import CollegeSettingsForm, InviteUserForm
from apps.web.mixins import CollegeAdminRequiredMixin

logger = logging.getLogger(__name__)


# ── College Settings ──────────────────────────────────────────

class CollegeSettingsView(CollegeAdminRequiredMixin, View):
    template_name = "web/college_admin/settings.html"

    def get(self, request):
        college  = request.college
        initial  = {
            "name":           college.name,
            "official_email": college.official_email,
            "official_phone": college.official_phone,
            "website_url":    college.website_url,
            "address_line1":  college.address_line1,
            "city":           college.city,
            "state":          college.state,
            "country":        college.country,
            "timezone":       college.timezone,
        }
        return render(request, self.template_name, {
            "page_title":    "College Settings",
            "page_subtitle": college.name,
            "form":          CollegeSettingsForm(initial=initial),
        })

    def post(self, request):
        college = request.college
        form    = CollegeSettingsForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {
                "page_title":    "College Settings",
                "page_subtitle": college.name,
                "form": form,
            })
        cd = form.cleaned_data
        college.name           = cd["name"]
        college.official_email = cd["official_email"]
        college.official_phone = cd["official_phone"]
        college.website_url    = cd["website_url"]
        college.address_line1  = cd["address_line1"]
        college.city           = cd["city"]
        college.state          = cd["state"]
        college.country        = cd["country"]
        college.timezone       = cd["timezone"]
        college.save()
        messages.success(request, "College settings updated.")
        return redirect("web:college_settings")


# ── User Management ───────────────────────────────────────────

class UserListView(CollegeAdminRequiredMixin, View):
    template_name = "web/college_admin/user_list.html"

    def get(self, request):
        college = request.college
        users   = (
            User.objects
            .filter(college=college)
            .prefetch_related("user_roles__role")
            .order_by("first_name", "last_name")
        )
        return render(request, self.template_name, {
            "page_title":    "Users",
            "page_subtitle": college.name,
            "users":         users,
        })


class InviteUserView(CollegeAdminRequiredMixin, View):
    template_name = "web/college_admin/invite_user.html"

    def get(self, request):
        return render(request, self.template_name, {
            "page_title": "Invite User",
            "form":       InviteUserForm(),
        })

    def post(self, request):
        college = request.college
        form    = InviteUserForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {
                "page_title": "Invite User",
                "form": form,
            })
        cd = form.cleaned_data
        with transaction.atomic():
            user = User.objects.create_user(
                email=cd["email"],
                password=cd["password"],
                first_name=cd["first_name"],
                last_name=cd.get("last_name") or "",
                phone=cd.get("phone") or "",
                college=college,
            )
            role, _ = Role.objects.get_or_create(
                code=cd["role"],
                defaults={
                    "name": cd["role"].replace("_", " ").title(),
                    "scope": "college",
                    "is_system_role": True,
                },
            )
            UserRole.objects.create(
                user=user,
                role=role,
                college=college,
                assigned_by=request.user,
                is_primary=True,
                status="active",
            )
        messages.success(request, f"User {user.email} added to {college.name}.")
        return redirect("web:user_list")


class UserDetailView(CollegeAdminRequiredMixin, View):
    """View / deactivate a single user within the college."""
    template_name = "web/college_admin/user_detail.html"

    def get(self, request, user_id):
        college = request.college
        user    = get_object_or_404(User, id=user_id, college=college)
        roles   = UserRole.objects.filter(user=user, college=college).select_related("role")
        return render(request, self.template_name, {
            "page_title":  user.get_full_name() or user.email,
            "viewed_user": user,
            "roles":       roles,
        })

    def post(self, request, user_id):
        """Toggle active/inactive status."""
        college = request.college
        user    = get_object_or_404(User, id=user_id, college=college)
        if user == request.user:
            messages.error(request, "You cannot deactivate your own account.")
            return redirect("web:user_detail", user_id=user_id)
        if user.status == UserStatus.ACTIVE:
            user.status    = UserStatus.INACTIVE
            user.is_active = False
            msg = f"{user.email} deactivated."
        else:
            user.status    = UserStatus.ACTIVE
            user.is_active = True
            msg = f"{user.email} reactivated."
        user.save(update_fields=["status", "is_active"])
        messages.success(request, msg)
        return redirect("web:user_list")


# ── Subscription Status ───────────────────────────────────────

class SubscriptionStatusView(CollegeAdminRequiredMixin, View):
    template_name = "web/college_admin/subscription.html"

    def get(self, request):
        college      = request.college
        subscription = SubscriptionService.get_active_subscription(college)
        entitlements = SubscriptionService.get_entitlements(college)
        all_subs     = (
            CollegeSubscription.objects
            .filter(college=college)
            .select_related("plan")
            .order_by("-created_at")
        )
        return render(request, self.template_name, {
            "page_title":    "Subscription",
            "page_subtitle": college.name,
            "subscription":  subscription,
            "entitlements":  entitlements,
            "all_subs":      all_subs,
        })
