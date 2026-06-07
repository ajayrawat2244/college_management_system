# apps/attendance/serializers.py
from rest_framework import serializers

from apps.attendance.models import AttendanceRecord, AttendanceSession


class AttendanceSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceSession
        fields = [
            "id", "college", "subject_offering", "session_date",
            "start_time", "end_time", "taken_by_teacher",
            "notes", "status", "created_at",
        ]
        read_only_fields = ["id", "college", "created_at"]


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    admission_no = serializers.CharField(source="enrollment.student.admission_no", read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = [
            "id", "college", "attendance_session", "enrollment",
            "student_name", "admission_no",
            "attendance_status", "marked_at", "marked_by", "remarks",
        ]
        read_only_fields = ["id", "college", "marked_at"]

    def get_student_name(self, obj):
        u = obj.enrollment.student.user
        return f"{u.first_name} {u.last_name or ''}".strip()


class BulkAttendanceRecordSerializer(serializers.Serializer):
    """
    Used for POST /attendance-sessions/{id}/mark-bulk/
    Accepts a list of { enrollment_id, attendance_status, remarks? }
    """
    enrollment_id = serializers.UUIDField()
    attendance_status = serializers.ChoiceField(
        choices=["present", "absent", "late", "excused"]
    )
    remarks = serializers.CharField(required=False, allow_blank=True)
