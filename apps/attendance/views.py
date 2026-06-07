# apps/attendance/views.py
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.attendance.models import AttendanceRecord, AttendanceSession
from apps.attendance.serializers import (
    AttendanceRecordSerializer,
    AttendanceSessionSerializer,
    BulkAttendanceRecordSerializer,
)
from apps.academics.models import Enrollment
from apps.platforms.mixins import CollegeScopedMixin
from apps.platforms.permissions import IsCollegeAdminOrTeacher, IsTenantResolved


class AttendanceSessionViewSet(CollegeScopedMixin, ModelViewSet):
    """
    Manage attendance sessions.
    Teachers create/close sessions; Admins have full access.
    """

    queryset = AttendanceSession.objects.select_related(
        "subject_offering", "taken_by_teacher"
    ).all().order_by("-session_date")
    serializer_class = AttendanceSessionSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdminOrTeacher]
    filterset_fields = ["subject_offering", "session_date", "status"]
    ordering_fields = ["session_date", "created_at"]

    @action(detail=True, methods=["post"], url_path="mark-bulk")
    def mark_bulk(self, request, pk=None):
        """
        POST /api/attendance/sessions/{id}/mark-bulk/
        Body: { "records": [ { enrollment_id, attendance_status, remarks? }, ... ] }

        Creates or updates attendance records for each enrollment in one call.
        Idempotent: re-submitting replaces existing records for this session.
        """
        session = self.get_object()
        college = self.get_college()

        if session.status == "cancelled":
            return Response(
                {"detail": "Cannot mark attendance for a cancelled session."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records_data = request.data.get("records", [])
        if not records_data:
            return Response(
                {"detail": "No records provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = BulkAttendanceRecordSerializer(data=records_data, many=True)
        serializer.is_valid(raise_exception=True)

        created_count = 0
        updated_count = 0
        errors = []

        for item in serializer.validated_data:
            try:
                enrollment = Enrollment.objects.get(
                    id=item["enrollment_id"], college=college
                )
                obj, created = AttendanceRecord.objects.update_or_create(
                    attendance_session=session,
                    enrollment=enrollment,
                    defaults={
                        "college": college,
                        "attendance_status": item["attendance_status"],
                        "marked_by": request.user,
                        "remarks": item.get("remarks", ""),
                    },
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Enrollment.DoesNotExist:
                errors.append(str(item["enrollment_id"]))

        return Response(
            {
                "detail": "Attendance marked.",
                "created": created_count,
                "updated": updated_count,
                "invalid_enrollments": errors,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="close")
    def close_session(self, request, pk=None):
        """POST /api/attendance/sessions/{id}/close/"""
        session = self.get_object()
        session.status = "closed"
        session.save(update_fields=["status"])
        return Response({"detail": "Session closed."})


class AttendanceRecordViewSet(CollegeScopedMixin, ModelViewSet):
    """Individual attendance record CRUD."""

    queryset = AttendanceRecord.objects.select_related(
        "attendance_session", "enrollment__student__user"
    ).all()
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdminOrTeacher]
    filterset_fields = ["attendance_session", "attendance_status", "enrollment"]
    ordering_fields = ["marked_at"]
