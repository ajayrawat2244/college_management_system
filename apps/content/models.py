#content/models.py
import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class MaterialType(models.TextChoices):
    NOTE = "note", "Note"
    PDF = "pdf", "PDF"
    LINK = "link", "Link"
    #VIDEO = "video", "Video"
    #AUDIO = "audio", "Audio"
    #IMAGE = "image", "Image"
    OTHER = "other", "Other"


class VisibilityScope(models.TextChoices):
    ALL = "all", "All"
    STUDENTS = "students", "Students"
    TEACHERS = "teachers", "Teachers"
    SECTION = "section", "Section"


class MaterialStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class AssignmentStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    CLOSED = "closed", "Closed"
    ARCHIVED = "archived", "Archived"


class SubmissionStatus(models.TextChoices):
    SUBMITTED = "submitted", "Submitted"
    LATE = "late", "Late"
    GRADED = "graded", "Graded"
    REJECTED = "rejected", "Rejected"


class NoticeAudience(models.TextChoices):
    ALL = "all", "All"
    STUDENTS = "students", "Students"
    TEACHERS = "teachers", "Teachers"
    STAFF = "staff", "Staff"
    SECTION = "section", "Section"
    ROLE = "role", "Role"


class NoticeStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class CourseMaterial(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="course_materials",
    )
    subject_offering = models.ForeignKey(
        "academics.SubjectOffering",
        on_delete=models.CASCADE,
        related_name="course_materials",
        null=True,
        blank=True,
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.CASCADE,
        related_name="course_materials",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    material_type = models.CharField(max_length=20, choices=MaterialType.choices)
    description = models.TextField(null=True, blank=True)
    file_asset = models.ForeignKey(
        "platforms.FileAsset",
        on_delete=models.SET_NULL,
        related_name="course_materials",
        null=True,
        blank=True,
    )
    external_url = models.TextField(null=True, blank=True)
    visibility = models.CharField(
        max_length=20,
        choices=VisibilityScope.choices,
        default=VisibilityScope.STUDENTS,
    )
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="created_course_materials",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=MaterialStatus.choices,
        default=MaterialStatus.DRAFT,
    )

    class Meta:
        db_table = "course_materials"
        constraints = [
            models.CheckConstraint(
                check=models.Q(subject_offering__isnull=False) | models.Q(subject__isnull=False),
                name="ck_course_material_subject_ref",
            )
        ]
        indexes = [
            models.Index(fields=["subject_offering"], name="idx_course_mat_suboff_id"),
        ]

    def __str__(self):
        return self.title


class Assignment(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    subject_offering = models.ForeignKey(
        "academics.SubjectOffering",
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    max_marks = models.DecimalField(max_digits=8, decimal_places=2, default=100)
    attachment_file_asset = models.ForeignKey(
        "platforms.FileAsset",
        on_delete=models.SET_NULL,
        related_name="assignment_attachments",
        null=True,
        blank=True,
    )
    created_by_teacher = models.ForeignKey(
        "accounts.TeacherProfile",
        on_delete=models.SET_NULL,
        related_name="assignments_created",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.DRAFT,
    )

    class Meta:
        db_table = "assignments"
        indexes = [
            models.Index(fields=["subject_offering"], name="idx_asg_suboff"),
        ]

    def __str__(self):
        return self.title


class AssignmentSubmission(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="assignment_submissions",
    )
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        "accounts.StudentProfile",
        on_delete=models.CASCADE,
        related_name="assignment_submissions",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    file_asset = models.ForeignKey(
        "platforms.FileAsset",
        on_delete=models.SET_NULL,
        related_name="assignment_submissions",
        null=True,
        blank=True,
    )
    submission_text = models.TextField(null=True, blank=True)
    marks_obtained = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    graded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="graded_submissions",
        null=True,
        blank=True,
    )
    graded_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.SUBMITTED,
    )

    class Meta:
        db_table = "assignment_submissions"
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "student"],
                name="uq_assignment_submission_per_student",
            )
        ]
        indexes = [
            models.Index(fields=["student"], name="idx_asgsub_std"),
        ]

    def __str__(self):
        return f"{self.assignment} - {self.student}"


class NoticeStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class Notice(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="notices",
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    audience_scope = models.CharField(max_length=20, choices=NoticeAudience.choices)
    target_section = models.ForeignKey(
        "academics.Section",
        on_delete=models.CASCADE,
        related_name="notices",
        null=True,
        blank=True,
    )
    target_role = models.ForeignKey(
        "accounts.Role",
        on_delete=models.SET_NULL,
        related_name="notices",
        null=True,
        blank=True,
    )
    file_asset = models.ForeignKey(
        "platforms.FileAsset",
        on_delete=models.SET_NULL,
        related_name="notices",
        null=True,
        blank=True,
    )
    published_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="published_notices",
        null=True,
        blank=True,
    )
    publish_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    priority = models.SmallIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=NoticeStatus.choices,
        default=NoticeStatus.DRAFT,
    )

    class Meta:
        db_table = "notices"
        indexes = [
            models.Index(
                fields=["college", "status", "publish_at"],
                name="idx_notices_clg_status_dt",
            ),
        ]

    def __str__(self):
        return self.title