# apps/web/auth/forms.py
from django import forms


class WebLoginForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "admin@college.com",
                "autocomplete": "email",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "••••••••",
                "autocomplete": "current-password",
            }
        ),
    )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class WebChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        label="Current password",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    new_password = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        min_length=8,
    )
    confirm_password = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password")
        p2 = cleaned.get("confirm_password")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("New passwords do not match.")
        return cleaned
