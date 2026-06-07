#attendance/models.py
import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class AttendanceSessionStatus(models.TextChoices):
    OPEN = "open", "Open"
    CLOSED = "closed", "Closed"
    CANCELLED = "cancelled", "Cancelled"


class AttendanceStatus(models.TextChoices):
    PRESENT = "present", "Present"
    ABSENT = "absent", "Absent"
    LATE = "late", "Late"
    EXCUSED = "excused", "Excused"


class AttendanceSession(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
    )
    subject_offering = models.ForeignKey(
        "academics.SubjectOffering",
        on_delete=models.CASCADE,
        related_name="attendance_sessions",
    )
    session_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    taken_by_teacher = models.ForeignKey(
        "accounts.TeacherProfile",
        on_delete=models.SET_NULL,
        related_name="attendance_sessions_taken",
        null=True,
        blank=True,
    )
    notes = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=AttendanceSessionStatus.choices,
        default=AttendanceSessionStatus.OPEN,
    )

    class Meta:
        db_table = "attendance_sessions"
        constraints = [
            models.UniqueConstraint(
                fields=["subject_offering", "session_date", "start_time"],
                name="uq_attendance_session_per_offering_date_start",
            )
        ]
        indexes = [
            models.Index(fields=["college", "session_date"], name="idx_att_sess_dt"),
        ]

    def __str__(self):
        return f"{self.subject_offering} - {self.session_date}"


class AttendanceRecord(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    attendance_session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name="records",
    )
    enrollment = models.ForeignKey(
        "academics.Enrollment",
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    attendance_status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices,
    )
    marked_at = models.DateTimeField(auto_now_add=True)
    marked_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="attendance_marked",
        null=True,
        blank=True,
    )
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "attendance_records"
        constraints = [
            models.UniqueConstraint(
                fields=["attendance_session", "enrollment"],
                name="uq_attendance_session_enrollment",
            )
        ]
        indexes = [
            models.Index(fields=["enrollment"], name="idx_att_rec_enr"),
        ]

    def __str__(self):
        return f"{self.enrollment} - {self.attendance_status}"