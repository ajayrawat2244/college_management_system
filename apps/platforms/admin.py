# apps/platforms/admin.py
from django.contrib import admin
from .models import (
    College, CollegeSettings, CollegeSubscription,
    Feature, FileAsset, PlanFeature,
    SubscriptionInvoice, SubscriptionPayment, SubscriptionPlan,
)

class PlanFeatureInline(admin.TabularInline):
    model = PlanFeature
    extra = 1
    autocomplete_fields = ("feature",)


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display  = ("name", "code", "subdomain", "status", "created_at")
    list_filter   = ("status",)
    search_fields = ("name", "code", "subdomain", "official_email")
    readonly_fields = ("id", "created_at", "updated_at")



@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display  = ("name", "code", "price_monthly", "price_yearly", "is_active", "sort_order")
    list_filter   = ("is_active",)
    search_fields = ("name", "code")
    inlines = [PlanFeatureInline]


@admin.register(CollegeSubscription)
class CollegeSubscriptionAdmin(admin.ModelAdmin):
    list_display  = ("college", "plan", "status", "billing_cycle", "trial_ends_at", "current_period_end")
    list_filter   = ("status", "billing_cycle")
    search_fields = ("college__name", "college__code")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display  = ("feature_code", "name", "module_name", "is_active")
    list_filter   = ("is_active", "module_name")
    search_fields = ("feature_code", "name", "module_name")


admin.register(PlanFeature)(admin.ModelAdmin)
admin.register(CollegeSettings)(admin.ModelAdmin)
admin.register(FileAsset)(admin.ModelAdmin)
admin.register(SubscriptionInvoice)(admin.ModelAdmin)
admin.register(SubscriptionPayment)(admin.ModelAdmin)
