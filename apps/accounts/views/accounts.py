# apps/accounts/views/accounts.py
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.accounts.models import Permission, Role, StudentProfile, TeacherProfile, User, UserRole
from apps.accounts.serializers import (
    CreateUserSerializer,
    PermissionSerializer,
    RoleSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
    UserSerializer,
)
from apps.platforms.mixins import CollegeScopedMixin
from apps.platforms.permissions import IsCollegeAdmin, IsSuperUser, IsTenantResolved


class UserViewSet(CollegeScopedMixin, ModelViewSet):
    """
    List / create / update users within the college tenant.
    SuperUser sees all users.
    College Admin sees only users in their college.
    """

    queryset = User.objects.select_related("college").prefetch_related("user_roles__role").all()
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["status", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["date_joined", "first_name"]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateUserSerializer
        return UserSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(college=self.get_college())

    def perform_create(self, serializer):
        serializer.save(college=self.get_college())

    @action(detail=True, methods=["post"], url_path="assign-role")
    def assign_role(self, request, pk=None):
        """POST /api/accounts/users/{id}/assign-role/ { role_id, is_primary }"""
        user = self.get_object()
        role_id = request.data.get("role_id")
        is_primary = request.data.get("is_primary", False)

        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            return Response({"detail": "Role not found."}, status=status.HTTP_404_NOT_FOUND)

        user_role, created = UserRole.objects.get_or_create(
            user=user,
            role=role,
            college=self.get_college(),
            defaults={"assigned_by": request.user, "is_primary": is_primary},
        )
        if not created:
            user_role.status = "active"
            user_role.save(update_fields=["status"])

        return Response({"detail": "Role assigned successfully."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="remove-role")
    def remove_role(self, request, pk=None):
        """POST /api/accounts/users/{id}/remove-role/ { role_id }"""
        user = self.get_object()
        role_id = request.data.get("role_id")
        updated = UserRole.objects.filter(
            user=user, role_id=role_id, college=self.get_college()
        ).update(status="inactive")
        if not updated:
            return Response({"detail": "Role assignment not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"detail": "Role removed."})


class RoleViewSet(ModelViewSet):
    """
    Manage roles. SuperUser can CRUD all roles.
    College Admin can only read.
    """

    queryset = Role.objects.prefetch_related("role_permissions__permission").all()
    serializer_class = RoleSerializer
    filterset_fields = ["scope", "status", "is_system_role"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsSuperUser()]


class PermissionViewSet(ReadOnlyModelViewSet):
    """Read-only list of all permissions."""

    queryset = Permission.objects.all().order_by("module_name", "name")
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, IsSuperUser]
    filterset_fields = ["module_name"]


class StudentProfileViewSet(CollegeScopedMixin, ModelViewSet):
    """
    Manage student profiles within the college.
    - College Admin: full CRUD
    - Teacher: read-only
    - Student: read own profile only
    """

    queryset = StudentProfile.objects.select_related("user", "college").all()
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["status", "gender"]
    search_fields = ["admission_no", "user__first_name", "user__last_name", "user__email"]
    ordering_fields = ["admission_no", "user__first_name"]

    @action(detail=False, methods=["get"], url_path="my-profile")
    def my_profile(self, request):
        """GET /api/accounts/students/my-profile/ — for the logged-in student."""
        try:
            profile = StudentProfile.objects.get(
                user=request.user, college=self.get_college()
            )
        except StudentProfile.DoesNotExist:
            return Response({"detail": "No student profile found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(StudentProfileSerializer(profile, context={"request": request}).data)


class TeacherProfileViewSet(CollegeScopedMixin, ModelViewSet):
    """
    Manage teacher profiles within the college.
    - College Admin: full CRUD
    - Teacher: read own profile only
    """

    queryset = TeacherProfile.objects.select_related("user", "college", "department").all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["status", "department"]
    search_fields = ["employee_no", "user__first_name", "user__last_name"]

    @action(detail=False, methods=["get"], url_path="my-profile")
    def my_profile(self, request):
        """GET /api/accounts/teachers/my-profile/ — for the logged-in teacher."""
        try:
            profile = TeacherProfile.objects.get(
                user=request.user, college=self.get_college()
            )
        except TeacherProfile.DoesNotExist:
            return Response({"detail": "No teacher profile found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(TeacherProfileSerializer(profile, context={"request": request}).data)
