#exams/models.py
import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class GradeScaleStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class ExamStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SCHEDULED = "scheduled", "Scheduled"
    CONDUCTED = "conducted", "Conducted"
    RESULT_DECLARED = "result_declared", "Result Declared"
    ARCHIVED = "archived", "Archived"


class ExamPaperStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    HELD = "held", "Held"
    CANCELLED = "cancelled", "Cancelled"


class ExamResultStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    FINALIZED = "finalized", "Finalized"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class GradingScale(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="grading_scales",
    )
    grade_label = models.CharField(max_length=10)
    min_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    max_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    grade_point = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=GradeScaleStatus.choices,
        default=GradeScaleStatus.ACTIVE,
    )

    class Meta:
        db_table = "grading_scales"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "grade_label"],
                name="uq_grade_label_per_college",
            )
        ]

    def __str__(self):
        return self.grade_label


class Exam(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="exams",
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.CASCADE,
        related_name="exams",
    )
    term = models.ForeignKey(
        "academics.Term",
        on_delete=models.SET_NULL,
        related_name="exams",
        null=True,
        blank=True,
    )
    section = models.ForeignKey(
        "academics.Section",
        on_delete=models.CASCADE,
        related_name="exams",
    )
    name = models.CharField(max_length=150)
    exam_type = models.CharField(
        max_length=30,
        choices=[
            ("unit", "Unit"),
            ("quiz", "Quiz"),
            ("midterm", "Midterm"),
            ("final", "Final"),
            ("practical", "Practical"),
            ("other", "Other"),
        ],
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ExamStatus.choices,
        default=ExamStatus.DRAFT,
    )

    class Meta:
        db_table = "exams"
        indexes = [
            models.Index(fields=["college", "section"], name="idx_exams_college_section"),
        ]

    def __str__(self):
        return self.name


class ExamPaperStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    HELD = "held", "Held"
    CANCELLED = "cancelled", "Cancelled"


class ExamPaper(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="exam_papers",
    )
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="papers",
    )
    subject_offering = models.ForeignKey(
        "academics.SubjectOffering",
        on_delete=models.CASCADE,
        related_name="exam_papers",
    )
    exam_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    max_marks = models.DecimalField(max_digits=8, decimal_places=2, default=100)
    pass_marks = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    room = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ExamPaperStatus.choices,
        default=ExamPaperStatus.SCHEDULED,
    )

    class Meta:
        db_table = "exam_papers"
        constraints = [
            models.UniqueConstraint(
                fields=["exam", "subject_offering"],
                name="uq_exam_paper_per_exam_subject",
            )
        ]
        indexes = [
            models.Index(fields=["exam"], name="idx_exam_papers_exam_id"),
        ]

    def __str__(self):
        return f"{self.exam} - {self.subject_offering}"


class ExamResultStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    FINALIZED = "finalized", "Finalized"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class ExamResult(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="exam_results",
    )
    exam_paper = models.ForeignKey(
        ExamPaper,
        on_delete=models.CASCADE,
        related_name="results",
    )
    student = models.ForeignKey(
        "accounts.StudentProfile",
        on_delete=models.CASCADE,
        related_name="exam_results",
    )
    marks_obtained = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    grade_label = models.CharField(max_length=10, null=True, blank=True)
    grade_point = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    evaluated_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="evaluated_exam_results",
        null=True,
        blank=True,
    )
    evaluated_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ExamResultStatus.choices,
        default=ExamResultStatus.DRAFT,
    )

    class Meta:
        db_table = "exam_results"
        constraints = [
            models.UniqueConstraint(
                fields=["exam_paper", "student"],
                name="uq_exam_result_per_paper_student",
            )
        ]
        indexes = [
            models.Index(fields=["student"], name="idx_exam_std"),
        ]

    def __str__(self):
        return f"{self.exam_paper} - {self.student}"