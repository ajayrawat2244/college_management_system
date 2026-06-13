# apps/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Permission, Role, RolePermission,
    StudentProfile, TeacherProfile,
    User, UserRole,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display    = ("email", "first_name", "last_name", "college", "status", "is_active", "date_joined")
    list_filter     = ("status", "is_active", "is_staff", "is_superuser")
    search_fields   = ("email", "first_name", "last_name")
    ordering        = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "last_login", "created_at", "updated_at")

    fieldsets = (
        (None,          {"fields": ("email", "password")}),
        ("Personal",    {"fields": ("first_name", "last_name", "phone", "avatar_url")}),
        ("College",     {"fields": ("college",)}),
        ("Status",      {"fields": ("status", "is_active", "is_staff", "is_superuser")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
        ("Timestamps",  {"fields": ("date_joined", "last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "college", "password1", "password2"),
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display  = ("code", "name", "scope", "is_system_role", "status")
    list_filter   = ("scope", "is_system_role", "status")
    search_fields = ("code", "name")


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display  = ("user", "role", "college", "is_primary", "status", "assigned_at")
    list_filter   = ("role", "is_primary", "status")
    search_fields = ("user__email", "college__name")
    readonly_fields = ("id", "assigned_at")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display  = ("admission_no", "user", "college", "status")
    list_filter   = ("status", "college")
    search_fields = ("admission_no", "user__email", "user__first_name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display  = ("employee_no", "user", "college", "designation", "status")
    list_filter   = ("status", "college")
    search_fields = ("employee_no", "user__email", "user__first_name")
    readonly_fields = ("created_at", "updated_at")


admin.site.register(Permission)
admin.site.register(RolePermission)
