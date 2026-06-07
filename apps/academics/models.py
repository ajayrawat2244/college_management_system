#academics/models.py
import uuid

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class DepartmentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class AcademicYearStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    ACTIVE = "active", "Active"
    CLOSED = "closed", "Closed"
    ARCHIVED = "archived", "Archived"


class ProgramLevel(models.TextChoices):
    DIPLOMA = "diploma", "Diploma"
    CERTIFICATE = "certificate", "Certificate"
    UNDERGRADUATE = "undergraduate", "Undergraduate"
    POSTGRADUATE = "postgraduate", "Postgraduate"
    DOCTORAL = "doctoral", "Doctoral"
    OTHER = "other", "Other"


class BatchStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class SectionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class SubjectType(models.TextChoices):
    CORE = "core", "Core"
    ELECTIVE = "elective", "Elective"
    LAB = "lab", "Lab"
    PROJECT = "project", "Project"
    OTHER = "other", "Other"


class SubjectStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class EnrollmentStatus(models.TextChoices):
    ENROLLED = "enrolled", "Enrolled"
    PROMOTED = "promoted", "Promoted"
    PASSED = "passed", "Passed"
    DROPPED = "dropped", "Dropped"
    TRANSFERRED = "transferred", "Transferred"
    COMPLETED = "completed", "Completed"


class YearStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class Department(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="departments",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=150)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=DepartmentStatus.choices,
        default=DepartmentStatus.ACTIVE,
    )

    class Meta:
        db_table = "departments"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "code"],
                name="uq_department_code_per_college",
            )
        ]
        indexes = [
            models.Index(fields=["college"], name="idx_dprtmts_col_id"),
        ]

    def __str__(self):
        return self.name


class AcademicYear(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="academic_years",
    )
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=AcademicYearStatus.choices,
        default=AcademicYearStatus.ACTIVE,
    )

    class Meta:
        db_table = "academic_years"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "name"],
                name="uq_academic_year_name_per_college",
            ),
            models.UniqueConstraint(
                fields=["college"],
                condition=models.Q(is_current=True),
                name="uq_current_academic_year_per_college",
            ),
        ]

    def __str__(self):
        return self.name


class TermStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    ACTIVE = "active", "Active"
    CLOSED = "closed", "Closed"
    ARCHIVED = "archived", "Archived"


class Term(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="terms",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="terms",
    )
    term_no = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=TermStatus.choices,
        default=TermStatus.ACTIVE,
    )

    class Meta:
        db_table = "terms"
        constraints = [
            models.UniqueConstraint(
                fields=["academic_year", "term_no"],
                name="uq_term_no_per_academic_year",
            )
        ]
        indexes = [
            models.Index(fields=["academic_year"], name="idx_terms_academicyear_id"),
        ]

    def __str__(self):
        return self.name


class ProgramStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class Program(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="programs",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        related_name="programs",
        null=True,
        blank=True,
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=150)
    level = models.CharField(max_length=30, choices=ProgramLevel.choices)
    duration_terms = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ProgramStatus.choices,
        default=ProgramStatus.ACTIVE,
    )

    class Meta:
        db_table = "programs"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "code"],
                name="uq_program_code_per_college",
            )
        ]
        indexes = [
            models.Index(fields=["college"], name="idx_programs_col_id"),
        ]

    def __str__(self):
        return self.name


class BatchStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class Batch(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="batches",
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="batches",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="batches",
    )
    name = models.CharField(max_length=100)
    intake_year = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=BatchStatus.choices,
        default=BatchStatus.ACTIVE,
    )

    class Meta:
        db_table = "batches"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "program", "academic_year", "name"],
                name="uq_batch_per_program_year_name",
            )
        ]
        indexes = [
            models.Index(fields=["program", "academic_year"], name="idx_batches_program_year"),
        ]

    def __str__(self):
        return self.name


class SectionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class Section(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="sections",
    )
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField(null=True, blank=True)
    room = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=SectionStatus.choices,
        default=SectionStatus.ACTIVE,
    )

    class Meta:
        db_table = "sections"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "batch", "name"],
                name="uq_section_name_per_batch",
            )
        ]
        indexes = [
            models.Index(fields=["batch"], name="idx_sections_batch_id"),
        ]

    def __str__(self):
        return self.name


class SubjectStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class Subject(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="subjects",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        related_name="subjects",
        null=True,
        blank=True,
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=150)
    credits = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    subject_type = models.CharField(max_length=20, choices=SubjectType.choices, default=SubjectType.CORE)
    status = models.CharField(
        max_length=20,
        choices=SubjectStatus.choices,
        default=SubjectStatus.ACTIVE,
    )

    class Meta:
        db_table = "subjects"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "code"],
                name="uq_subject_code_per_college",
            )
        ]
        indexes = [
            models.Index(fields=["college"], name="idx_subjects_col_id"),
        ]

    def __str__(self):
        return self.name


class SubjectOfferingStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class SubjectOffering(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="subject_offerings",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="subject_offerings",
    )
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name="subject_offerings",
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="subject_offerings",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="offerings",
    )
    teacher = models.ForeignKey(
        "accounts.TeacherProfile",
        on_delete=models.SET_NULL,
        related_name="subject_offerings",
        null=True,
        blank=True,
    )
    lecture_hours_per_week = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    room = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=SubjectOfferingStatus.choices,
        default=SubjectOfferingStatus.ACTIVE,
    )

    class Meta:
        db_table = "subject_offerings"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "section", "subject", "term"],
                name="uq_subject_offering_per_section_subject_term",
            )
        ]
        indexes = [
            models.Index(fields=["section"], name="idx_suboff_sec"),
            models.Index(fields=["teacher"], name="idx_suboff_tchr"),
        ]

    def __str__(self):
        return f"{self.section} - {self.subject}"


class EnrollmentStatus(models.TextChoices):
    ENROLLED = "enrolled", "Enrolled"
    PROMOTED = "promoted", "Promoted"
    PASSED = "passed", "Passed"
    DROPPED = "dropped", "Dropped"
    TRANSFERRED = "transferred", "Transferred"
    COMPLETED = "completed", "Completed"


class Enrollment(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    student = models.ForeignKey(
        "accounts.StudentProfile",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    admission_date = models.DateField(auto_now_add=True)
    roll_no = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=EnrollmentStatus.choices,
        default=EnrollmentStatus.ENROLLED,
    )

    class Meta:
        db_table = "enrollments"
        constraints = [
            models.UniqueConstraint(
                fields=["college", "student", "academic_year"],
                name="uq_student_per_academic_year_per_college",
            ),
            models.UniqueConstraint(
                fields=["college", "section", "roll_no"],
                name="uq_roll_no_per_section_per_college",
            ),
        ]
        indexes = [
            models.Index(fields=["section"], name="idx_enroll_section_id"),
            models.Index(fields=["student"], name="idx_enroll_stdt_id"),
        ]

    def __str__(self):
        return f"{self.student} - {self.section}"


class DayOfWeek(models.IntegerChoices):
    MONDAY = 1, "Monday"
    TUESDAY = 2, "Tuesday"
    WEDNESDAY = 3, "Wednesday"
    THURSDAY = 4, "Thursday"
    FRIDAY = 5, "Friday"
    SATURDAY = 6, "Saturday"
    SUNDAY = 7, "Sunday"


class TimetableEntryStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    CANCELLED = "cancelled", "Cancelled"


class TimetableEntry(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.CASCADE,
        related_name="timetable_entries",
    )
    subject_offering = models.ForeignKey(
        SubjectOffering,
        on_delete=models.CASCADE,
        related_name="timetable_entries",
    )
    day_of_week = models.PositiveSmallIntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=TimetableEntryStatus.choices,
        default=TimetableEntryStatus.ACTIVE,
    )

    class Meta:
        db_table = "timetable_entries"
        constraints = [
            models.UniqueConstraint(
                fields=["subject_offering", "day_of_week", "start_time"],
                name="uq_timetable_entry_per_offering_day_start",
            )
        ]
        indexes = [
            models.Index(fields=["college", "day_of_week"], name="idx_tt_entries_clg_day"),
        ]

    def __str__(self):
        return f"{self.subject_offering} - {self.day_of_week}"