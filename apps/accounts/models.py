#accounts/models.py
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class UserStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    BLOCKED = "blocked", "Blocked"
    ARCHIVED = "archived", "Archived"


class RoleScope(models.TextChoices):
    PLATFORM = "platform", "Platform"
    COLLEGE = "college", "College"


class RoleStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class Permission(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    module_name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "permissions"

    def __str__(self):
        return self.code


class Role(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    scope = models.CharField(max_length=20, choices=RoleScope.choices)
    is_system_role = models.BooleanField(default=True)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=RoleStatus.choices,
        default=RoleStatus.ACTIVE,
    )

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="permission_roles",
    )

    class Meta:
        db_table = "role_permissions"
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="uq_role_permission",
            )
        ]

    def __str__(self):
        return f"{self.role} - {self.permission}"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("status", UserStatus.ACTIVE)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.SET_NULL,
        related_name="users",
        null=True,
        blank=True,
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    avatar_url = models.TextField(null=True, blank=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=timezone.now)

    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]

    objects = UserManager()

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["college"], name="idx_users_clg_id"),
            models.Index(fields=["status"], name="idx_users_status"),
        ]

    def __str__(self):
        return self.email


class UserRole(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="user_roles")
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="assigned_roles",
        null=True,
        blank=True,
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="roles_assigned",
        null=True,
        blank=True,
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default="active")

    class Meta:
        db_table = "user_roles"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role", "college"],
                name="uq_user_role_college",
            )
        ]
        indexes = [
            models.Index(fields=["user", "college"], name="idx_userroles_user_col"),
            models.Index(fields=["role"], name="idx_userroles_role_id"),
        ]

    def __str__(self):
        return f"{self.user} - {self.role}"


class StudentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    LEFT = "left", "Left"
    GRADUATED = "graduated", "Graduated"
    SUSPENDED = "suspended", "Suspended"


class TeacherStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    RESIGNED = "resigned", "Resigned"
    RETIRED = "retired", "Retired"
    ON_LEAVE = "on_leave", "On Leave"


class GenderChoices(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"
    UNSPECIFIED = "unspecified", "Unspecified"


class StudentProfile(TimeStampedModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
        primary_key=True,
    )
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="student_profiles",
    )
    admission_no = models.CharField(max_length=50)
    photo_file_asset = models.ForeignKey(
        "platforms.FileAsset",
        on_delete=models.SET_NULL,
        related_name="student_photos",
        null=True,
        blank=True,
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=20,
        choices=GenderChoices.choices,
        default=GenderChoices.UNSPECIFIED,
    )
    guardian_name = models.CharField(max_length=150, null=True, blank=True)
    guardian_phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=StudentStatus.choices,
        default=StudentStatus.ACTIVE,
    )

    class Meta:
        db_table = "student_profiles"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "admission_no"],
                name="uq_student_admission_no_per_college",
            )
        ]
        indexes = [
            models.Index(fields=["college"], name="idx_std_prof_col_id"),
        ]

    def __str__(self):
        return self.admission_no


class TeacherProfile(TimeStampedModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        primary_key=True,
    )
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="teacher_profiles",
    )
    employee_no = models.CharField(max_length=50)
    department = models.ForeignKey(
        "academics.Department",
        on_delete=models.SET_NULL,
        related_name="teachers",
        null=True,
        blank=True,
    )
    designation = models.CharField(max_length=100, null=True, blank=True)
    qualification = models.CharField(max_length=255, null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    photo_file_asset = models.ForeignKey(
        "platforms.FileAsset",
        on_delete=models.SET_NULL,
        related_name="teacher_photos",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=TeacherStatus.choices,
        default=TeacherStatus.ACTIVE,
    )

    class Meta:
        db_table = "teacher_profiles"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "employee_no"],
                name="uq_teacher_employee_no_per_college",
            )
        ]
        indexes = [
            models.Index(fields=["college"], name="idx_tchr_prof_col_id"),
            models.Index(fields=["department"], name="idx_tchr_prof_dept_id"),
        ]

    def __str__(self):
        return self.employee_no