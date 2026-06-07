#finance/models.py
import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class FeeHeadCategory(models.TextChoices):
    TUITION = "tuition", "Tuition"
    EXAM = "exam", "Exam"
    LIBRARY = "library", "Library"
    HOSTEL = "hostel", "Hostel"
    TRANSPORT = "transport", "Transport"
    LAB = "lab", "Lab"
    MISC = "misc", "Misc"


class FeeHeadStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class FeeStructureStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class StudentFeeAccountStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    CLOSED = "closed", "Closed"
    SUSPENDED = "suspended", "Suspended"


class FeeInvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ISSUED = "issued", "Issued"
    PART_PAID = "part_paid", "Part Paid"
    PAID = "paid", "Paid"
    OVERDUE = "overdue", "Overdue"
    VOID = "void", "Void"


class FeePaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESSFUL = "successful", "Successful"
    FAILED = "failed", "Failed"
    REVERSED = "reversed", "Reversed"


class PaymentMode(models.TextChoices):
    CASH = "cash", "Cash"
    CARD = "card", "Card"
    UPI = "upi", "UPI"
    NETBANKING = "netbanking", "Net Banking"
    BANK_TRANSFER = "bank_transfer", "Bank Transfer"
    CHEQUE = "cheque", "Cheque"
    ONLINE = "online", "Online"


class FeeHead(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="fee_heads",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=30, choices=FeeHeadCategory.choices)
    default_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_optional = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=FeeHeadStatus.choices,
        default=FeeHeadStatus.ACTIVE,
    )

    class Meta:
        db_table = "fee_heads"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "code"],
                name="uq_fee_head_code_per_college",
            )
        ]

    def __str__(self):
        return self.name


class FeeStructure(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="fee_structures",
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.CASCADE,
        related_name="fee_structures",
    )
    program = models.ForeignKey(
        "academics.Program",
        on_delete=models.CASCADE,
        related_name="fee_structures",
    )
    section = models.ForeignKey(
        "academics.Section",
        on_delete=models.CASCADE,
        related_name="fee_structures",
        null=True,
        blank=True,
    )
    term = models.ForeignKey(
        "academics.Term",
        on_delete=models.CASCADE,
        related_name="fee_structures",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=150)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=FeeStructureStatus.choices,
        default=FeeStructureStatus.ACTIVE,
    )

    class Meta:
        db_table = "fee_structures"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "academic_year", "program", "section", "name"],
                name="uq_fee_structure_per_scope_name",
            )
        ]
        indexes = [
            models.Index(fields=["college", "program", "academic_year"], name="idx_feestr_prog"),
        ]

    def __str__(self):
        return self.name


class FeeStructureItem(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="fee_structure_items",
    )
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.CASCADE,
        related_name="items",
    )
    fee_head = models.ForeignKey(
        FeeHead,
        on_delete=models.PROTECT,
        related_name="structure_items",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    sort_order = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        choices=FeeStructureStatus.choices,
        default=FeeStructureStatus.ACTIVE,
    )

    class Meta:
        db_table = "fee_structure_items"
        constraints = [
            models.UniqueConstraint(
                fields=["fee_structure", "fee_head"],
                name="uq_fee_structure_item_per_head",
            )
        ]

    def __str__(self):
        return f"{self.fee_structure} - {self.fee_head}"


class StudentFeeAccountStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    CLOSED = "closed", "Closed"
    SUSPENDED = "suspended", "Suspended"


class StudentFeeAccount(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="student_fee_accounts",
    )
    student = models.OneToOneField(
        "accounts.StudentProfile",
        on_delete=models.CASCADE,
        related_name="fee_account",
    )
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.PROTECT,
        related_name="student_fee_accounts",
    )
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=StudentFeeAccountStatus.choices,
        default=StudentFeeAccountStatus.ACTIVE,
    )

    class Meta:
        db_table = "student_fee_accounts"
        constraints = [
            models.UniqueConstraint(
                fields=["student"],
                name="uq_one_fee_account_per_student",
            )
        ]
        indexes = [
            models.Index(fields=["college"], name="idx_stdfee_col"),
        ]

    def __str__(self):
        return f"{self.student}"


class FeeInvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ISSUED = "issued", "Issued"
    PART_PAID = "part_paid", "Part Paid"
    PAID = "paid", "Paid"
    OVERDUE = "overdue", "Overdue"
    VOID = "void", "Void"


class FeeInvoice(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="fee_invoices",
    )
    student_fee_account = models.ForeignKey(
        StudentFeeAccount,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    invoice_no = models.CharField(max_length=50)
    invoice_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    issued_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="issued_fee_invoices",
        null=True,
        blank=True,
    )
    notes = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=FeeInvoiceStatus.choices,
        default=FeeInvoiceStatus.ISSUED,
    )

    class Meta:
        db_table = "fee_invoices"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "invoice_no"],
                name="uq_fee_invoice_no_per_college",
            )
        ]
        indexes = [
            models.Index(fields=["student_fee_account"], name="idx_fee_invoices_account_id"),
            models.Index(fields=["college", "status", "due_date"], name="idx_feeinv_due"),
        ]

    def __str__(self):
        return self.invoice_no


class FeeInvoiceItem(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="fee_invoice_items",
    )
    fee_invoice = models.ForeignKey(
        FeeInvoice,
        on_delete=models.CASCADE,
        related_name="items",
    )
    fee_head = models.ForeignKey(
        FeeHead,
        on_delete=models.PROTECT,
        related_name="invoice_items",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[("active", "Active"), ("void", "Void")],
        default="active",
    )

    class Meta:
        db_table = "fee_invoice_items"
        constraints = [
            models.UniqueConstraint(
                fields=["fee_invoice", "fee_head"],
                name="uq_fee_invoice_item_per_head",
            )
        ]

    def __str__(self):
        return f"{self.fee_invoice} - {self.fee_head}"


class FeePaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESSFUL = "successful", "Successful"
    FAILED = "failed", "Failed"
    REVERSED = "reversed", "Reversed"


class FeePayment(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="fee_payments",
    )
    fee_invoice = models.ForeignKey(
        FeeInvoice,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    receipt_no = models.CharField(max_length=50)
    payment_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_mode = models.CharField(max_length=30, choices=PaymentMode.choices)
    reference_no = models.CharField(max_length=100, null=True, blank=True)
    received_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="received_fee_payments",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=FeePaymentStatus.choices,
        default=FeePaymentStatus.SUCCESSFUL,
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "fee_payments"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "receipt_no"],
                name="uq_fee_receipt_no_per_college",
            )
        ]
        indexes = [
            models.Index(fields=["fee_invoice"], name="idx_fee_payments_invoice_id"),
        ]

    def __str__(self):
        return self.receipt_no