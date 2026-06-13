# apps/web/onboarding/forms.py
"""
Forms for the 3-step public college registration wizard.

  Step 1: College details + admin account
  Step 2: Subscription plan + billing cycle
  Step 3: Subdomain + final confirmation
"""
import re
from django import forms
from apps.platforms.models import College, SubscriptionPlan

_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9\-]{0,60}[a-z0-9])?$")


class CollegeInfoForm(forms.Form):
    """Step 1 — Institution details + admin account."""

    # Institution
    college_name  = forms.CharField(
        label="College / Institution name", max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "e.g. Sunrise College of Engineering"}),
    )
    college_code  = forms.CharField(
        label="Short code", max_length=50,
        help_text="2–10 uppercase letters/numbers. Must be unique.",
        widget=forms.TextInput(attrs={"placeholder": "e.g. SCE"}),
    )
    official_email = forms.EmailField(
        label="Official email",
        widget=forms.EmailInput(attrs={"placeholder": "admin@sunrise.edu"}),
    )
    official_phone = forms.CharField(
        label="Phone number", max_length=20, required=False,
        widget=forms.TextInput(attrs={"placeholder": "+91 98765 43210"}),
    )
    city    = forms.CharField(max_length=100, required=False)
    state   = forms.CharField(max_length=100, required=False)
    country = forms.CharField(max_length=100, required=False, initial="India")

    # Admin account
    admin_first_name     = forms.CharField(label="Your first name", max_length=150)
    admin_last_name      = forms.CharField(label="Your last name",  max_length=150, required=False)
    admin_email          = forms.EmailField(label="Your login email")
    admin_password       = forms.CharField(
        label="Password", min_length=8,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    admin_password_confirm = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean_college_code(self):
        code = self.cleaned_data["college_code"].strip().upper()
        if College.objects.filter(code=code).exists():
            raise forms.ValidationError("This college code is already taken.")
        return code

    def clean_admin_email(self):
        from apps.accounts.models import User
        email = self.cleaned_data["admin_email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists. Try logging in instead."
            )
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("admin_password")
        p2 = cleaned.get("admin_password_confirm")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class PlanSelectionForm(forms.Form):
    """Step 2 — Subscription plan and billing cycle."""

    plan = forms.ModelChoiceField(
        queryset=SubscriptionPlan.objects.filter(is_active=True).order_by("sort_order"),
        label="Select a plan",
        empty_label=None,
        widget=forms.RadioSelect,
    )
    billing_cycle = forms.ChoiceField(
        choices=[("monthly", "Monthly"), ("yearly", "Yearly  —  save ~15%")],
        initial="monthly",
        widget=forms.RadioSelect,
    )


class DomainSetupForm(forms.Form):
    """Step 3 — Choose subdomain slug."""

    subdomain = forms.SlugField(
        label="Subdomain",
        max_length=120,
        help_text=(
            "Lowercase letters, numbers, and hyphens only. "
            "Cannot start or end with a hyphen."
        ),
        widget=forms.TextInput(attrs={"placeholder": "sunrise-college"}),
    )

    def clean_subdomain(self):
        value = self.cleaned_data["subdomain"].strip().lower()
        if not _SLUG_RE.match(value):
            raise forms.ValidationError(
                "Use only lowercase letters, numbers, and hyphens. "
                "Cannot start or end with a hyphen."
            )
        if College.objects.filter(subdomain=value).exists():
            raise forms.ValidationError("This subdomain is already taken.")
        return value
