# apps/finance/serializers.py
from rest_framework import serializers

from apps.finance.models import (
    FeeHead,
    FeeInvoice,
    FeeInvoiceItem,
    FeePayment,
    FeeStructure,
    FeeStructureItem,
    StudentFeeAccount,
)


class FeeHeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeHead
        fields = [
            "id", "college", "code", "name", "category",
            "default_amount", "is_optional", "status",
        ]
        read_only_fields = ["id", "college"]


class FeeStructureItemSerializer(serializers.ModelSerializer):
    fee_head_name = serializers.CharField(source="fee_head.name", read_only=True)

    class Meta:
        model = FeeStructureItem
        fields = ["id", "college", "fee_structure", "fee_head", "fee_head_name", "amount", "sort_order", "status"]
        read_only_fields = ["id", "college"]


class FeeStructureSerializer(serializers.ModelSerializer):
    items = FeeStructureItemSerializer(many=True, read_only=True)

    class Meta:
        model = FeeStructure
        fields = [
            "id", "college", "academic_year", "program", "section", "term",
            "name", "total_amount", "status", "items",
        ]
        read_only_fields = ["id", "college"]


class StudentFeeAccountSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentFeeAccount
        fields = [
            "id", "college", "student", "student_name", "fee_structure",
            "opening_balance", "current_balance", "status",
        ]
        read_only_fields = ["id", "college"]

    def get_student_name(self, obj):
        u = obj.student.user
        return f"{u.first_name} {u.last_name or ''}".strip()


class FeeInvoiceItemSerializer(serializers.ModelSerializer):
    fee_head_name = serializers.CharField(source="fee_head.name", read_only=True)

    class Meta:
        model = FeeInvoiceItem
        fields = ["id", "college", "fee_invoice", "fee_head", "fee_head_name", "amount", "status"]
        read_only_fields = ["id", "college"]


class FeeInvoiceSerializer(serializers.ModelSerializer):
    items = FeeInvoiceItemSerializer(many=True, read_only=True)

    class Meta:
        model = FeeInvoice
        fields = [
            "id", "college", "student_fee_account", "invoice_no",
            "invoice_date", "due_date", "total_amount",
            "paid_amount", "balance_amount", "issued_by",
            "notes", "status", "items", "created_at",
        ]
        read_only_fields = ["id", "college", "invoice_date", "issued_by", "created_at"]


class FeePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeePayment
        fields = [
            "id", "college", "fee_invoice", "receipt_no",
            "payment_date", "amount", "payment_mode",
            "reference_no", "received_by", "status", "metadata",
        ]
        read_only_fields = ["id", "college", "payment_date", "received_by"]
