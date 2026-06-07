# apps/finance/views.py
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.finance.models import (
    FeeHead,
    FeeInvoice,
    FeeInvoiceItem,
    FeePayment,
    FeeStructure,
    FeeStructureItem,
    StudentFeeAccount,
)
from apps.finance.serializers import (
    FeeHeadSerializer,
    FeeInvoiceSerializer,
    FeePaymentSerializer,
    FeeStructureItemSerializer,
    FeeStructureSerializer,
    StudentFeeAccountSerializer,
)
from apps.platforms.mixins import CollegeScopedMixin
from apps.platforms.permissions import IsCollegeAdmin, IsTenantResolved


class FeeHeadViewSet(CollegeScopedMixin, ModelViewSet):
    queryset = FeeHead.objects.all().order_by("name")
    serializer_class = FeeHeadSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["category", "status", "is_optional"]
    search_fields = ["name", "code"]


class FeeStructureViewSet(CollegeScopedMixin, ModelViewSet):
    queryset = FeeStructure.objects.prefetch_related("items__fee_head").all()
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["academic_year", "program", "section", "status"]
    search_fields = ["name"]


class StudentFeeAccountViewSet(CollegeScopedMixin, ModelViewSet):
    """
    One fee account per student. College Admin creates/manages.
    Students can GET their own account.
    """

    queryset = StudentFeeAccount.objects.select_related(
        "student__user", "fee_structure"
    ).all()
    serializer_class = StudentFeeAccountSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["status", "fee_structure"]
    search_fields = ["student__admission_no", "student__user__first_name"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if hasattr(user, "student_profile"):
            return qs.filter(student=user.student_profile)
        return qs


class FeeInvoiceViewSet(CollegeScopedMixin, ModelViewSet):
    """Fee invoices with line items."""

    queryset = FeeInvoice.objects.prefetch_related("items__fee_head").all().order_by("-invoice_date")
    serializer_class = FeeInvoiceSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["status", "student_fee_account"]

    def perform_create(self, serializer):
        serializer.save(college=self.get_college(), issued_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="record-payment")
    def record_payment(self, request, pk=None):
        """
        POST /api/finance/invoices/{id}/record-payment/
        Body: { amount, payment_mode, receipt_no, reference_no? }
        Atomically records a payment and updates the invoice balance.
        """
        from django.db import transaction

        invoice = self.get_object()
        amount = request.data.get("amount")
        payment_mode = request.data.get("payment_mode")
        receipt_no = request.data.get("receipt_no")

        if not all([amount, payment_mode, receipt_no]):
            return Response(
                {"detail": "amount, payment_mode, and receipt_no are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return Response({"detail": "Invalid amount."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            payment = FeePayment.objects.create(
                college=self.get_college(),
                fee_invoice=invoice,
                receipt_no=receipt_no,
                amount=amount,
                payment_mode=payment_mode,
                reference_no=request.data.get("reference_no", ""),
                received_by=request.user,
                status="successful",
            )

            invoice.paid_amount = float(invoice.paid_amount) + amount
            invoice.balance_amount = float(invoice.total_amount) - float(invoice.paid_amount)
            if invoice.balance_amount <= 0:
                invoice.status = "paid"
            elif invoice.paid_amount > 0:
                invoice.status = "part_paid"
            invoice.save(update_fields=["paid_amount", "balance_amount", "status"])

        return Response(
            FeePaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )


class FeePaymentViewSet(CollegeScopedMixin, ModelViewSet):
    """Read-only view of payments; creation is via invoice.record-payment."""

    queryset = FeePayment.objects.select_related(
        "fee_invoice", "received_by"
    ).all().order_by("-payment_date")
    serializer_class = FeePaymentSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["status", "payment_mode", "fee_invoice"]
    http_method_names = ["get", "head", "options"]
