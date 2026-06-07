# apps/exams/views.py
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.exams.models import Exam, ExamPaper, ExamResult, GradingScale
from apps.exams.serializers import (
    ExamPaperSerializer,
    ExamResultSerializer,
    ExamSerializer,
    GradingScaleSerializer,
)
from apps.platforms.mixins import CollegeScopedMixin
from apps.platforms.permissions import (
    HasFeatureAccess,
    IsCollegeAdmin,
    IsCollegeAdminOrTeacher,
    IsTenantResolved,
)


class GradingScaleViewSet(CollegeScopedMixin, ModelViewSet):
    queryset = GradingScale.objects.all().order_by("-min_percentage")
    serializer_class = GradingScaleSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["status"]


class ExamViewSet(CollegeScopedMixin, ModelViewSet):
    queryset = Exam.objects.select_related(
        "academic_year", "term", "section"
    ).all().order_by("-start_date")
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdminOrTeacher]
    filterset_fields = ["academic_year", "term", "section", "exam_type", "status"]
    search_fields = ["name"]


class ExamPaperViewSet(CollegeScopedMixin, ModelViewSet):
    queryset = ExamPaper.objects.select_related(
        "exam", "subject_offering__subject"
    ).all().order_by("exam_date", "start_time")
    serializer_class = ExamPaperSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdminOrTeacher]
    filterset_fields = ["exam", "subject_offering", "status"]


class ExamResultViewSet(CollegeScopedMixin, ModelViewSet):
    """
    Exam results — gated by the 'exam_results' feature flag.
    Teachers can create/update; Students can read their own.
    """

    queryset = ExamResult.objects.select_related(
        "exam_paper__exam", "student__user", "evaluated_by"
    ).all()
    serializer_class = ExamResultSerializer
    permission_classes = [
        IsAuthenticated,
        IsTenantResolved,
        IsCollegeAdminOrTeacher,
        HasFeatureAccess,
    ]
    required_feature = "exam_results"
    filterset_fields = ["exam_paper", "student", "status"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if hasattr(user, "student_profile"):
            return qs.filter(student=user.student_profile)
        return qs

    def perform_create(self, serializer):
        serializer.save(
            college=self.get_college(),
            evaluated_by=self.request.user,
            evaluated_at=timezone.now(),
        )

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """POST /api/exams/results/{id}/publish/"""
        result = self.get_object()
        result.status = "published"
        result.save(update_fields=["status"])
        return Response({"detail": "Result published."})

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create(self, request):
        """
        POST /api/exams/results/bulk-create/
        Body: { "exam_paper_id": "...", "results": [ { student_id, marks_obtained, ... } ] }
        """
        college = self.get_college()
        exam_paper_id = request.data.get("exam_paper_id")
        results_data = request.data.get("results", [])

        if not exam_paper_id or not results_data:
            return Response(
                {"detail": "exam_paper_id and results are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = []
        for item in results_data:
            obj, _ = ExamResult.objects.update_or_create(
                exam_paper_id=exam_paper_id,
                student_id=item["student_id"],
                defaults={
                    "college": college,
                    "marks_obtained": item.get("marks_obtained"),
                    "grade_label": item.get("grade_label", ""),
                    "grade_point": item.get("grade_point"),
                    "remarks": item.get("remarks", ""),
                    "evaluated_by": request.user,
                    "evaluated_at": timezone.now(),
                    "status": "draft",
                },
            )
            created.append(str(obj.id))

        return Response({"detail": f"{len(created)} results saved.", "ids": created})
