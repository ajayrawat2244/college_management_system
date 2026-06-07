# apps/content/views.py
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.content.models import Assignment, AssignmentSubmission, CourseMaterial, Notice
from apps.content.serializers import (
    AssignmentSerializer,
    AssignmentSubmissionSerializer,
    CourseMaterialSerializer,
    NoticeSerializer,
)
from apps.platforms.mixins import CollegeScopedMixin
from apps.platforms.permissions import (
    HasFeatureAccess,
    IsCollegeAdmin,
    IsCollegeAdminOrTeacher,
    IsTenantResolved,
)


class CourseMaterialViewSet(CollegeScopedMixin, ModelViewSet):
    """
    Course materials — Teachers create, Students read published ones.
    """

    queryset = CourseMaterial.objects.select_related(
        "subject_offering", "subject", "created_by"
    ).all().order_by("-created_at")
    serializer_class = CourseMaterialSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdminOrTeacher]
    filterset_fields = ["subject_offering", "subject", "material_type", "status", "visibility"]
    search_fields = ["title"]

    def perform_create(self, serializer):
        serializer.save(college=self.get_college(), created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """POST /api/content/materials/{id}/publish/"""
        material = self.get_object()
        material.is_published = True
        material.published_at = timezone.now()
        material.status = "published"
        material.save(update_fields=["is_published", "published_at", "status"])
        return Response({"detail": "Material published."})


class AssignmentViewSet(CollegeScopedMixin, ModelViewSet):
    """Assignments — Teachers create and manage."""

    queryset = Assignment.objects.select_related(
        "subject_offering", "created_by_teacher"
    ).all().order_by("-created_at")
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdminOrTeacher]
    filterset_fields = ["subject_offering", "status"]
    search_fields = ["title"]

    def perform_create(self, serializer):
        teacher = getattr(self.request.user, "teacher_profile", None)
        serializer.save(college=self.get_college(), created_by_teacher=teacher)


class AssignmentSubmissionViewSet(CollegeScopedMixin, ModelViewSet):
    """
    Assignment submissions.
    - Students create/update their own submission.
    - Teachers grade submissions.
    """

    queryset = AssignmentSubmission.objects.select_related(
        "assignment", "student__user", "graded_by"
    ).all()
    serializer_class = AssignmentSubmissionSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved]
    filterset_fields = ["assignment", "status"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Students see only their own submissions
        if hasattr(user, "student_profile"):
            return qs.filter(student=user.student_profile)
        return qs

    @action(detail=True, methods=["patch"], url_path="grade")
    def grade(self, request, pk=None):
        """PATCH /api/content/submissions/{id}/grade/ { marks_obtained }"""
        submission = self.get_object()
        marks = request.data.get("marks_obtained")
        if marks is None:
            return Response(
                {"detail": "marks_obtained is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        submission.marks_obtained = marks
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.status = "graded"
        submission.save(update_fields=["marks_obtained", "graded_by", "graded_at", "status"])
        return Response(AssignmentSubmissionSerializer(submission).data)


class NoticeViewSet(CollegeScopedMixin, ModelViewSet):
    """College-wide notices."""

    queryset = Notice.objects.all().order_by("-priority", "-publish_at")
    serializer_class = NoticeSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["status", "audience_scope", "target_section"]
    search_fields = ["title"]

    def perform_create(self, serializer):
        serializer.save(college=self.get_college(), published_by=self.request.user)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        notice = self.get_object()
        notice.status = "published"
        notice.publish_at = timezone.now()
        notice.save(update_fields=["status", "publish_at"])
        return Response({"detail": "Notice published."})
