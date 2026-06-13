# apps/web/college_admin/forms.py
"""
Forms used by the College Admin section.
"""
from django import forms
from django.core.validators import RegexValidator

from apps.accounts.models import GenderChoices, User, UserStatus
from apps.platforms.models import College


class CollegeSettingsForm(forms.Form):
    """Edit basic college profile information."""
    name           = forms.CharField(max_length=255)
    official_email = forms.EmailField(required=False)
    official_phone = forms.CharField(max_length=20, required=False)
    website_url    = forms.URLField(required=False, label="Website URL")
    address_line1  = forms.CharField(max_length=255, required=False, label="Address line 1")
    city           = forms.CharField(max_length=100, required=False)
    state          = forms.CharField(max_length=100, required=False)
    country        = forms.CharField(max_length=100, required=False)
    timezone       = forms.ChoiceField(
        choices=[
            ("Asia/Kolkata",    "Asia/Kolkata (IST)"),
            ("Asia/Dubai",      "Asia/Dubai (GST)"),
            ("Europe/London",   "Europe/London (GMT/BST)"),
            ("America/New_York","America/New_York (EST/EDT)"),
            ("UTC",             "UTC"),
        ],
        initial="Asia/Kolkata",
    )


class InviteUserForm(forms.Form):
    """Invite a new user to the college (admin creates their account)."""
    first_name = forms.CharField(max_length=150)
    last_name  = forms.CharField(max_length=150, required=False)
    email      = forms.EmailField()
    phone      = forms.CharField(max_length=20, required=False)
    role       = forms.ChoiceField(choices=[
        ("college_admin", "College Admin"),
        ("teacher",       "Teacher"),
        ("student",       "Student"),
    ])
    password   = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Minimum 8 characters.",
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email
