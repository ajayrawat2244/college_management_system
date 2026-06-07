# apps/accounts/urls/accounts.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views.accounts import (
    PermissionViewSet,
    RoleViewSet,
    StudentProfileViewSet,
    TeacherProfileViewSet,
    UserViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")
router.register("roles", RoleViewSet, basename="role")
router.register("permissions", PermissionViewSet, basename="permission")
router.register("students", StudentProfileViewSet, basename="student-profile")
router.register("teachers", TeacherProfileViewSet, basename="teacher-profile")

urlpatterns = [
    path("", include(router.urls)),
]
