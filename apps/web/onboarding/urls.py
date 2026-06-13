# apps/web/onboarding/urls.py
from django.urls import path
from apps.web.onboarding.views import (
    OnboardingSuccessView,
    Step1CollegeInfoView,
    Step2PlanView,
    Step3DomainView,
)

urlpatterns = [
    path("",         Step1CollegeInfoView.as_view(), name="register_step1"),
    path("plan/",    Step2PlanView.as_view(),        name="register_step2"),
    path("domain/",  Step3DomainView.as_view(),      name="register_step3"),
    path("success/", OnboardingSuccessView.as_view(), name="register_success"),
]
