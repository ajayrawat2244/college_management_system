# apps/web/onboarding/views.py
"""
Public college registration — 3-step session-backed wizard.

Session key: ``onboarding_wizard`` (dict with step data).

Step 1 → /register/           (CollegeInfoForm)
Step 2 → /register/plan/      (PlanSelectionForm)
Step 3 → /register/domain/    (DomainSetupForm + final commit)

On successful Step 3 commit:
  - College is created
  - Admin User is created and assigned college_admin role
  - CollegeSubscription (trial) is created
  - User is logged in automatically
  - Redirect → college dashboard (subdomain-based)
"""
import logging
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.db import transaction
from django.shortcuts import redirect, render
from django.views import View

from apps.accounts.models import Role, User, UserRole
from apps.platforms.models import (
    College,
    CollegeSettings,
    CollegeStatus,
    CollegeSubscription,
    PlanBillingCycle,
    SubscriptionStatus,
)
from apps.web.onboarding.forms import CollegeInfoForm, DomainSetupForm, PlanSelectionForm

logger = logging.getLogger(__name__)

_SESSION_KEY = "onboarding_wizard"

STEPS = {
    1: "College Info",
    2: "Choose Plan",
    3: "Domain Setup",
}
TOTAL_STEPS = len(STEPS)


def _wizard_data(request):
    return request.session.get(_SESSION_KEY, {})


def _save_wizard(request, data):
    existing = _wizard_data(request)
    existing.update(data)
    request.session[_SESSION_KEY] = existing
    request.session.modified = True


def _clear_wizard(request):
    request.session.pop(_SESSION_KEY, None)


class Step1CollegeInfoView(View):
    """GET/POST /register/ — Step 1: college details + admin account."""

    template_name = "web/onboarding/step1_college_info.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("web:dashboard")
        saved = _wizard_data(request).get("step1", {})
        form = CollegeInfoForm(initial=saved)
        return render(request, self.template_name, self._ctx(form))

    def post(self, request):
        form = CollegeInfoForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._ctx(form))
        _save_wizard(request, {"step1": form.cleaned_data})
        return redirect("web:register_step2")

    @staticmethod
    def _ctx(form):
        return {
            "form": form,
            "current_step": 1,
            "total_steps": TOTAL_STEPS,
            "step_name": STEPS[1],
        }


class Step2PlanView(View):
    """GET/POST /register/plan/ — Step 2: choose subscription plan."""

    template_name = "web/onboarding/step2_plan.html"

    def _guard(self, request):
        """Redirect back to step 1 if step 1 data is missing."""
        if not _wizard_data(request).get("step1"):
            return redirect("web:register_step1")
        return None

    def get(self, request):
        guard = self._guard(request)
        if guard:
            return guard
        saved = _wizard_data(request).get("step2", {})
        form = PlanSelectionForm(initial=saved)
        return render(request, self.template_name, self._ctx(form))

    def post(self, request):
        guard = self._guard(request)
        if guard:
            return guard
        form = PlanSelectionForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._ctx(form))
        _save_wizard(request, {
            "step2": {
                "plan_id": str(form.cleaned_data["plan"].id),
                "plan_name": form.cleaned_data["plan"].name,
                "billing_cycle": form.cleaned_data["billing_cycle"],
            }
        })
        return redirect("web:register_step3")

    @staticmethod
    def _ctx(form):
        return {
            "form": form,
            "current_step": 2,
            "total_steps": TOTAL_STEPS,
            "step_name": STEPS[2],
        }


class Step3DomainView(View):
    """GET/POST /register/domain/ — Step 3: choose subdomain + final commit."""

    template_name = "web/onboarding/step3_domain.html"

    def _guard(self, request):
        data = _wizard_data(request)
        if not data.get("step1"):
            return redirect("web:register_step1")
        if not data.get("step2"):
            return redirect("web:register_step2")
        return None

    def get(self, request):
        guard = self._guard(request)
        if guard:
            return guard
        saved = _wizard_data(request).get("step3", {})
        form = DomainSetupForm(initial=saved)
        return render(request, self.template_name, self._ctx(request, form))

    def post(self, request):
        guard = self._guard(request)
        if guard:
            return guard
        form = DomainSetupForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._ctx(request, form))

        _save_wizard(request, {"step3": form.cleaned_data})

        try:
            user, college = self._commit(request)
        except Exception as exc:
            logger.exception("Onboarding commit failed: %s", exc)
            messages.error(
                request,
                "Something went wrong during registration. Please try again.",
            )
            return render(request, self.template_name, self._ctx(request, form))

        _clear_wizard(request)
        login(request, user)
        messages.success(
            request,
            f"Welcome! Your college workspace ", {college.name}, " is ready.",
        )
        return redirect("web:dashboard")

    @staticmethod
    @transaction.atomic
    def _commit(request):
        """Create College, User (admin), UserRole, CollegeSubscription atomically."""
        from apps.platforms.models import SubscriptionPlan

        data = _wizard_data(request)
        s1 = data["step1"]
        s2 = data["step2"]
        s3 = data["step3"]

        # 1. Create College
        college = College.objects.create(
            name=s1["college_name"],
            code=s1["college_code"],
            slug=s3["subdomain"],
            subdomain=s3["subdomain"],
            official_email=s1["official_email"],
            official_phone=s1.get("official_phone", ""),
            city=s1.get("city", ""),
            state=s1.get("state", ""),
            country=s1.get("country", "India"),
            status=CollegeStatus.ACTIVE,
        )

        # 2. Create CollegeSettings (defaults)
        CollegeSettings.objects.create(college=college)

        # 3. Create admin User
        user = User.objects.create_user(
            email=s1["admin_email"],
            password=s1["admin_password"],
            first_name=s1["admin_first_name"],
            last_name=s1.get("admin_last_name", ""),
            college=college,
        )

        # 4. Assign college_admin role (must exist as a seed Role)
        admin_role, _ = Role.objects.get_or_create(
            code="college_admin",
            defaults={
                "name": "College Admin",
                "scope": "college",
                "is_system_role": True,
            },
        )
        UserRole.objects.create(
            user=user,
            role=admin_role,
            college=college,
            assigned_by=None,
            is_primary=True,
            status="active",
        )

        # 5. Create trial CollegeSubscription
        plan = SubscriptionPlan.objects.get(id=s2["plan_id"])
        billing_cycle = s2["billing_cycle"]
        trial_end = date.today() + timedelta(days=14)
        CollegeSubscription.objects.create(
            college=college,
            plan=plan,
            status=SubscriptionStatus.TRIAL,
            billing_cycle=(
                PlanBillingCycle.MONTHLY
                if billing_cycle == "monthly"
                else PlanBillingCycle.YEARLY
            ),
            trial_ends_at=trial_end,
            current_period_start=date.today(),
            current_period_end=trial_end,
            auto_renew=True,
        )

        logger.info(
            "Onboarding: created college=%s user=%s plan=%s",
            college.code,
            user.email,
            plan.code,
        )
        return user, college

    @staticmethod
    def _ctx(request, form):
        data = _wizard_data(request)
        return {
            "form": form,
            "current_step": 3,
            "total_steps": TOTAL_STEPS,
            "step_name": STEPS[3],
            "plan_name": data.get("step2", {}).get("plan_name", ""),
            "billing_cycle": data.get("step2", {}).get("billing_cycle", "monthly"),
            "college_name": data.get("step1", {}).get("college_name", ""),
        }


class OnboardingSuccessView(View):
    """Fallback success page (normally the wizard redirects straight to dashboard)."""

    template_name = "web/onboarding/success.html"

    def get(self, request):
        return render(request, self.template_name)
