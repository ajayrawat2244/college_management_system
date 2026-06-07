# apps/accounts/serializers.py
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import (
    Permission,
    Role,
    RolePermission,
    StudentProfile,
    TeacherProfile,
    User,
    UserRole,
)


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "code", "name", "module_name", "description"]
        read_only_fields = ["id"]


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ["id", "code", "name", "scope", "is_system_role", "description", "status", "permissions"]
        read_only_fields = ["id"]

    def get_permissions(self, obj):
        codes = obj.role_permissions.values_list("permission__code", flat=True)
        return list(codes)


class UserRoleSerializer(serializers.ModelSerializer):
    role_code = serializers.CharField(source="role.code", read_only=True)
    role_name = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = UserRole
        fields = ["id", "role", "role_code", "role_name", "college", "is_primary", "status", "assigned_at"]
        read_only_fields = ["id", "assigned_at"]


class UserSerializer(serializers.ModelSerializer):
    user_roles = UserRoleSerializer(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "phone", "avatar_url", "college", "status",
            "is_staff", "is_superuser", "date_joined", "user_roles",
        ]
        read_only_fields = ["id", "email", "is_staff", "is_superuser", "date_joined", "college"]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name or ''}".strip()


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "phone", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user", write_only=True
    )

    class Meta:
        model = StudentProfile
        fields = [
            "user", "user_id", "college", "admission_no",
            "photo_file_asset", "date_of_birth", "gender",
            "guardian_name", "guardian_phone", "address",
            "emergency_contact", "status",
        ]
        read_only_fields = ["college"]


class TeacherProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source="user", write_only=True
    )

    class Meta:
        model = TeacherProfile
        fields = [
            "user", "user_id", "college", "employee_no",
            "department", "designation", "qualification",
            "joining_date", "photo_file_asset", "status",
        ]
        read_only_fields = ["college"]
