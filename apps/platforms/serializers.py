# apps/platforms/serializers.py
from rest_framework import serializers

from apps.platforms.models import (
    College,
    CollegeSettings,
    CollegeSubscription,
    Feature,
    FileAsset,
    PlanFeature,
    SubscriptionInvoice,
    SubscriptionPayment,
    SubscriptionPlan,
)


class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        model = College
        fields = [
            "id", "code", "name", "slug", "subdomain",
            "official_email", "official_phone", "website_url",
            "address_line1", "address_line2", "city", "state",
            "postal_code", "country", "timezone", "status",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CollegeSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollegeSettings
        fields = [
            "college", "logo_file_asset", "default_currency",
            "academic_year_start_month", "feature_overrides", "settings_jsonb",
        ]
        read_only_fields = ["college"]


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ["id", "feature_code", "name", "module_name", "description", "is_active"]


class PlanFeatureSerializer(serializers.ModelSerializer):
    feature = FeatureSerializer(read_only=True)
    feature_id = serializers.PrimaryKeyRelatedField(
        queryset=Feature.objects.all(), source="feature", write_only=True
    )

    class Meta:
        model = PlanFeature
        fields = ["id", "feature", "feature_id", "is_enabled", "limit_value", "notes"]


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    plan_features = PlanFeatureSerializer(many=True, read_only=True)

    class Meta:
        model = SubscriptionPlan
        fields = [
            "id", "code", "name", "billing_cycle",
            "price_monthly", "price_yearly", "currency",
            "sort_order", "is_active", "description", "plan_features",
        ]
        read_only_fields = ["id"]


class CollegeSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.all(), source="plan", write_only=True
    )

    class Meta:
        model = CollegeSubscription
        fields = [
            "id", "college", "plan", "plan_id", "status", "billing_cycle",
            "trial_ends_at", "current_period_start", "current_period_end",
            "auto_renew", "cancelled_at", "ended_at",
            "entitlements_snapshot", "notes", "created_at",
        ]
        read_only_fields = ["id", "college", "created_at", "entitlements_snapshot"]


class SubscriptionInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionInvoice
        fields = [
            "id", "college", "subscription", "invoice_no", "invoice_date",
            "due_date", "currency", "amount_due", "amount_paid",
            "balance_due", "status", "notes", "created_at",
        ]
        read_only_fields = ["id", "college", "invoice_date", "created_at"]


class SubscriptionPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPayment
        fields = [
            "id", "college", "invoice", "payment_ref", "amount",
            "payment_mode", "paid_at", "status", "metadata",
        ]
        read_only_fields = ["id", "college", "paid_at"]


class FileAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileAsset
        fields = [
            "id", "college", "uploaded_by", "storage_backend",
            "storage_key", "original_name", "mime_type",
            "file_size", "checksum", "asset_kind", "metadata", "created_at",
        ]
        read_only_fields = [
            "id", "college", "uploaded_by", "storage_backend",
            "storage_key", "checksum", "created_at",
        ]
