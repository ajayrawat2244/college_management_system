# apps/finance/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.finance.views import (
    FeeHeadViewSet,
    FeeInvoiceViewSet,
    FeePaymentViewSet,
    FeeStructureViewSet,
    StudentFeeAccountViewSet,
)

router = DefaultRouter()
router.register("fee-heads", FeeHeadViewSet, basename="fee-head")
router.register("fee-structures", FeeStructureViewSet, basename="fee-structure")
router.register("student-accounts", StudentFeeAccountViewSet, basename="student-fee-account")
router.register("invoices", FeeInvoiceViewSet, basename="fee-invoice")
router.register("payments", FeePaymentViewSet, basename="fee-payment")

urlpatterns = [path("", include(router.urls))]
