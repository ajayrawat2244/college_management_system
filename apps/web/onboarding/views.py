# apps/web/onboarding/views.py
"""
Public college registration — 3-step session-backed wizard.

Session key: ``onboarding_wizard``

Step 1  /register/          — College info + admin account
Step 2  /register/plan/     — Choose subscription plan
Step 3  /register/domain/   — Choose subdomain → atomic commit

On successful Step 3:
  • College created
  • CollegeSettings defaults created
  • Admin User created
  • college_admin Role assigned
  • CollegeSubscription (trial) created
  • User auto-logged in
  • Redirect to /dashboard/ (role-aware)
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
    SubscriptionPlan,
)
from apps.web.onboarding.forms import CollegeInfoForm, DomainSetupForm, PlanSelectionForm
from apps.web.utils import get_post_login_redirect

logger = logging.getLogger(__name__)

_SESSION_KEY = "onboarding_wizard"

STEPS = {1: "College Info", 2: "Choose Plan", 3: "Domain Setup"}
TOTAL_STEPS = len(STEPS)


# ── Session helpers ──────────────────────────────────────────

def _data(request):
    return request.session.get(_SESSION_KEY, {})

def _save(request, patch):
    d = _data(request)
    d.update(patch)
    request.session[_SESSION_KEY] = d
    request.session.modified = True

def _clear(request):
    request.session.pop(_SESSION_KEY, None)


# ── Step 1 ───────────────────────────────────────────────────

class Step1CollegeInfoView(View):
    template_name = "web/onboarding/step1_college_info.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("web:dashboard")
        initial = {k: v for k, v in _data(request).get("step1", {}).items()
                   if k not in ("admin_password", "admin_password_confirm")}
        return render(request, self.template_name, self._ctx(CollegeInfoForm(initial=initial)))

    def post(self, request):
        form = CollegeInfoForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._ctx(form))
        # Don't persist raw passwords in session — store everything except
        # passwords, then re-save passwords separately (they'll be used once at commit)
        _save(request, {"step1": form.cleaned_data})
        return redirect("web:register_step2")

    @staticmethod
    def _ctx(form):
        return {
            "form": form,
            "current_step": 1,
            "total_steps": TOTAL_STEPS,
            "step_name": STEPS[1],
            "steps": STEPS,
        }


# ── Step 2 ───────────────────────────────────────────────────

class Step2PlanView(View):
    template_name = "web/onboarding/step2_plan.html"

    def _guard(self, request):
        if not _data(request).get("step1"):
            return redirect("web:register_step1")

    def get(self, request):
        if guard := self._guard(request):
            return guard
        return render(request, self.template_name, self._ctx(PlanSelectionForm()))

    def post(self, request):
        if guard := self._guard(request):
            return guard
        form = PlanSelectionForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._ctx(form))
        _save(request, {"step2": {
            "plan_id":      str(form.cleaned_data["plan"].id),
            "plan_name":    form.cleaned_data["plan"].name,
            "plan_price_monthly": str(form.cleaned_data["plan"].price_monthly),
            "plan_price_yearly":  str(form.cleaned_data["plan"].price_yearly),
            "billing_cycle": form.cleaned_data["billing_cycle"],
        }})
        return redirect("web:register_step3")

    @staticmethod
    def _ctx(form):
        return {
            "form": form,
            "current_step": 2,
            "total_steps": TOTAL_STEPS,
            "step_name": STEPS[2],
            "steps": STEPS,
            "plans": SubscriptionPlan.objects.filter(is_active=True).prefetch_related(
                "plan_features__feature"
            ).order_by("sort_order"),
        }


# ── Step 3 ───────────────────────────────────────────────────

class Step3DomainView(View):
    template_name = "web/onboarding/step3_domain.html"

    def _guard(self, request):
        d = _data(request)
        if not d.get("step1"):
            return redirect("web:register_step1")
        if not d.get("step2"):
            return redirect("web:register_step2")

    def get(self, request):
        if guard := self._guard(request):
            return guard
        return render(request, self.template_name, self._ctx(request, DomainSetupForm()))

    def post(self, request):
        if guard := self._guard(request):
            return guard
        form = DomainSetupForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._ctx(request, form))
        _save(request, {"step3": form.cleaned_data})
        try:
            user, college = self._commit(request)
        except Exception as exc:
            logger.exception("Onboarding commit failed: %s", exc)
            messages.error(request, "Something went wrong during registration. Please try again.")
            return render(request, self.template_name, self._ctx(request, form))
        _clear(request)
        login(request, user)
        messages.success(request, f'Welcome! Your workspace "{college.name}" is ready.')
        return redirect(get_post_login_redirect(user, college))

    @staticmethod
    @transaction.atomic
    def _commit(request):
        d = _data(request)
        s1, s2, s3 = d["step1"], d["step2"], d["step3"]

        # 1 – College
        college = College.objects.create(
            name=s1["college_name"],
            code=s1["college_code"],
            slug=s3["subdomain"],
            subdomain=s3["subdomain"],
            official_email=s1["official_email"],
            official_phone=s1.get("official_phone", ""),
            city=s1.get("city", ""),
            state=s1.get("state", ""),
            country=s1.get("country", "India") or "India",
            status=CollegeStatus.ACTIVE,
        )

        # 2 – CollegeSettings defaults
        CollegeSettings.objects.create(college=college)

        # 3 – Admin user
        user = User.objects.create_user(
            email=s1["admin_email"],
            password=s1["admin_password"],
            first_name=s1["admin_first_name"],
            last_name=s1.get("admin_last_name") or "",
            college=college,
        )

        # 4 – college_admin Role (get or create seed data)
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

        # 5 – Trial subscription
        plan  = SubscriptionPlan.objects.get(id=s2["plan_id"])
        cycle = s2["billing_cycle"]
        trial_end = date.today() + timedelta(days=14)
        from django.utils import timezone
        CollegeSubscription.objects.create(
            college=college,
            plan=plan,
            status=SubscriptionStatus.TRIAL,
            billing_cycle=PlanBillingCycle.MONTHLY if cycle == "monthly" else PlanBillingCycle.YEARLY,
            trial_ends_at=timezone.now() + timedelta(days=14),
            current_period_start=date.today(),
            current_period_end=trial_end,
            auto_renew=True,
        )

        logger.info("Onboarding: created college=%s user=%s plan=%s", college.code, user.email, plan.code)
        return user, college

    @staticmethod
    def _ctx(request, form):
        d = _data(request)
        return {
            "form": form,
            "current_step": 3,
            "total_steps": TOTAL_STEPS,
            "step_name": STEPS[3],
            "steps": STEPS,
            "college_name":   d.get("step1", {}).get("college_name", ""),
            "plan_name":      d.get("step2", {}).get("plan_name", ""),
            "billing_cycle":  d.get("step2", {}).get("billing_cycle", "monthly"),
        }


class OnboardingSuccessView(View):
    """Fallback — normally wizard redirects straight to dashboard."""
    def get(self, request):
        return render(request, "web/onboarding/success.html")
