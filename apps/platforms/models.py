#platforms/models.py
import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class CollegeStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    SUSPENDED = "suspended", "Suspended"
    ARCHIVED = "archived", "Archived"


class PlanBillingCycle(models.TextChoices):
    MONTHLY = "monthly", "Monthly"
    YEARLY = "yearly", "Yearly"


class SubscriptionStatus(models.TextChoices):
    TRIAL = "trial", "Trial"
    ACTIVE = "active", "Active"
    PAST_DUE = "past_due", "Past Due"
    CANCELLED = "cancelled", "Cancelled"
    EXPIRED = "expired", "Expired"


class InvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ISSUED = "issued", "Issued"
    OVERDUE = "overdue", "Overdue"
    PAID = "paid", "Paid"
    VOID = "void", "Void"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESSFUL = "successful", "Successful"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"


class PaymentMode(models.TextChoices):
    CASH = "cash", "Cash"
    CARD = "card", "Card"
    UPI = "upi", "UPI"
    NETBANKING = "netbanking", "Net Banking"
    BANK_TRANSFER = "bank_transfer", "Bank Transfer"
    CHEQUE = "cheque", "Cheque"
    ONLINE = "online", "Online"


class FileStorageBackend(models.TextChoices):
    LOCAL = "local", "Local"
    S3 = "s3", "S3"
    GCS = "gcs", "GCS"
    AZURE = "azure", "Azure"
    OTHER = "other", "Other"


class AssetKind(models.TextChoices):
    PROFILE_PHOTO = "profile_photo", "Profile Photo"
    DOCUMENT = "document", "Document"
    IMAGE = "image", "Image"
    VIDEO = "video", "Video"
    AUDIO = "audio", "Audio"
    PDF = "pdf", "PDF"
    GENERAL = "general", "General"


class College(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=120, unique=True)
    subdomain = models.CharField(max_length=120, unique=True, null=True, blank=True)

    official_email = models.EmailField(null=True, blank=True)
    official_phone = models.CharField(max_length=20, null=True, blank=True)
    website_url = models.URLField(null=True, blank=True)

    address_line1 = models.TextField(null=True, blank=True)
    address_line2 = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, default="India")
    timezone = models.CharField(max_length=64, default="Asia/Kolkata")

    status = models.CharField(
        max_length=20,
        choices=CollegeStatus.choices,
        default=CollegeStatus.ACTIVE,
    )

    class Meta:
        db_table = "colleges"
        indexes = [
            models.Index(fields=["status"], name="idx_colleges_status"),
        ]

    def __str__(self):
        return self.name


class Feature(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feature_code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    module_name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "feature_catalog"

    def __str__(self):
        return self.feature_code


class SubscriptionPlan(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    billing_cycle = models.CharField(
        max_length=20,
        choices=PlanBillingCycle.choices,
    )
    price_monthly = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    price_yearly = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="INR")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "subscription_plans"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class PlanFeature(models.Model):
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name="plan_features",
    )
    feature = models.ForeignKey(
        Feature,
        on_delete=models.CASCADE,
        related_name="feature_plans",
    )
    is_enabled = models.BooleanField(default=True)
    limit_value = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "plan_features"
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "feature"],
                name="uq_plan_feature",
            )
        ]
        indexes = [
            models.Index(fields=["feature"], name="idx_plan_features_feature_id"),
        ]

    def __str__(self):
        return f"{self.plan} - {self.feature}"


class CollegeSubscription(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="subscriptions",
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="college_subscriptions",
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.TRIAL,
    )
    billing_cycle = models.CharField(
        max_length=20,
        choices=PlanBillingCycle.choices,
    )
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateField()
    current_period_end = models.DateField()
    auto_renew = models.BooleanField(default=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    entitlements_snapshot = models.JSONField(default=dict, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "college_subscriptions"
        indexes = [
            models.Index(
                fields=["college", "status"],
                name="idx_colsub_stat",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["college"],
                condition=models.Q(status__in=["trial", "active", "past_due"]),
                name="uq_one_active_subscription_per_college",
            )
        ]

    def __str__(self):
        return f"{self.college} - {self.plan}"


class SubscriptionInvoice(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="subscription_invoices",
    )
    subscription = models.ForeignKey(
        CollegeSubscription,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    invoice_no = models.CharField(max_length=50)
    invoice_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="INR")
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.ISSUED,
    )
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "subscription_invoices"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "invoice_no"],
                name="uq_subscription_invoice_no_per_college",
            )
        ]
        indexes = [
            models.Index(
                fields=["college", "status", "due_date"],
                name="idx_subinv_stat",
            ),
        ]

    def __str__(self):
        return self.invoice_no


class SubscriptionPayment(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="subscription_payments",
    )
    invoice = models.ForeignKey(
        SubscriptionInvoice,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    payment_ref = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_mode = models.CharField(max_length=30, choices=PaymentMode.choices)
    paid_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.SUCCESSFUL,
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "subscription_payments"
        indexes = [
            models.Index(fields=["invoice"], name="idx_subpay_inv"),
        ]

    def __str__(self):
        return self.payment_ref


class FileAsset(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="file_assets",
        null=True,
        blank=True,
    )
    uploaded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="uploaded_assets",
        null=True,
        blank=True,
    )
    storage_backend = models.CharField(
        max_length=30,
        choices=FileStorageBackend.choices,
        default=FileStorageBackend.LOCAL,
    )
    storage_key = models.TextField()
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100, null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=128, null=True, blank=True)
    asset_kind = models.CharField(
        max_length=50,
        choices=AssetKind.choices,
        default=AssetKind.GENERAL,
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "file_assets"
        indexes = [
            models.Index(fields=["college"], name="idx_file_assets_clg_id"),
            models.Index(fields=["uploaded_by"], name="idx_file_user"),
        ]

    def __str__(self):
        return self.original_name


class CollegeSettings(TimeStampedModel):
    college = models.OneToOneField(
        College,
        on_delete=models.CASCADE,
        related_name="settings",
        primary_key=True,
    )
    logo_file_asset = models.ForeignKey(
        FileAsset,
        on_delete=models.SET_NULL,
        related_name="used_as_logo_for",
        null=True,
        blank=True,
    )
    default_currency = models.CharField(max_length=3, default="INR")
    academic_year_start_month = models.PositiveSmallIntegerField(default=7)
    feature_overrides = models.JSONField(default=dict, blank=True)
    settings_jsonb = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "college_settings"

    def __str__(self):
        return f"Settings for {self.college}"