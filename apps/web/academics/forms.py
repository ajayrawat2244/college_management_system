# apps/web/academics/forms.py
"""
Forms for the academics web module.
All dropdowns are scoped to request.college at instantiation time.
"""
from django import forms

from apps.academics.models import (
    AcademicYear, AcademicYearStatus,
    Batch, BatchStatus,
    Department, DepartmentStatus,
    DayOfWeek,
    Enrollment, EnrollmentStatus,
    Program, ProgramLevel, ProgramStatus,
    Section, SectionStatus,
    Subject, SubjectType, SubjectStatus,
    SubjectOffering, SubjectOfferingStatus,
    Term, TermStatus,
)


class DepartmentForm(forms.Form):
    code        = forms.CharField(max_length=50, widget=forms.TextInput(attrs={"placeholder": "e.g. CS"}))
    name        = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"placeholder": "e.g. Computer Science"}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))
    status      = forms.ChoiceField(choices=DepartmentStatus.choices, initial=DepartmentStatus.ACTIVE)


class AcademicYearForm(forms.Form):
    name       = forms.CharField(max_length=50, widget=forms.TextInput(attrs={"placeholder": "e.g. 2024-25"}))
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date   = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    is_current = forms.BooleanField(required=False, label="Set as current year")
    status     = forms.ChoiceField(choices=AcademicYearStatus.choices, initial=AcademicYearStatus.ACTIVE)

    def clean(self):
        cleaned = super().clean()
        s, e = cleaned.get("start_date"), cleaned.get("end_date")
        if s and e and e <= s:
            raise forms.ValidationError("End date must be after start date.")
        return cleaned


class TermForm(forms.Form):
    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            self.fields["academic_year"].queryset = AcademicYear.objects.filter(college=college).order_by("-start_date")

    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.none(), empty_label="Select year")
    term_no       = forms.IntegerField(min_value=1, max_value=12, label="Term number")
    name          = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"placeholder": "e.g. Semester 1"}))
    start_date    = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date      = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    is_current    = forms.BooleanField(required=False, label="Set as current term")
    status        = forms.ChoiceField(choices=TermStatus.choices, initial=TermStatus.ACTIVE)


class ProgramForm(forms.Form):
    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            self.fields["department"].queryset = Department.objects.filter(college=college, status="active").order_by("name")

    code           = forms.CharField(max_length=50)
    name           = forms.CharField(max_length=150)
    level          = forms.ChoiceField(choices=ProgramLevel.choices)
    department     = forms.ModelChoiceField(queryset=Department.objects.none(), required=False, empty_label="No department")
    duration_terms = forms.IntegerField(required=False, min_value=1, label="Duration (terms)")
    status         = forms.ChoiceField(choices=ProgramStatus.choices, initial=ProgramStatus.ACTIVE)


class BatchForm(forms.Form):
    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            self.fields["program"].queryset = Program.objects.filter(college=college, status="active").order_by("name")
            self.fields["academic_year"].queryset = AcademicYear.objects.filter(college=college).order_by("-start_date")

    program       = forms.ModelChoiceField(queryset=Program.objects.none(), empty_label="Select program")
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.none(), empty_label="Select year")
    name          = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"placeholder": "e.g. Batch 2024"}))
    intake_year   = forms.IntegerField(required=False, label="Intake year")
    status        = forms.ChoiceField(choices=BatchStatus.choices, initial=BatchStatus.ACTIVE)


class SectionForm(forms.Form):
    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            self.fields["batch"].queryset = (
                Batch.objects.filter(college=college, status="active")
                .select_related("program")
                .order_by("program__name", "name")
            )

    batch    = forms.ModelChoiceField(queryset=Batch.objects.none(), empty_label="Select batch")
    name     = forms.CharField(max_length=50, widget=forms.TextInput(attrs={"placeholder": "e.g. A, B, or Morning"}))
    capacity = forms.IntegerField(required=False, min_value=1, label="Capacity (optional)")
    room     = forms.CharField(max_length=50, required=False)
    status   = forms.ChoiceField(choices=SectionStatus.choices, initial=SectionStatus.ACTIVE)


class SubjectForm(forms.Form):
    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            self.fields["department"].queryset = Department.objects.filter(college=college, status="active").order_by("name")

    code         = forms.CharField(max_length=50)
    name         = forms.CharField(max_length=150)
    credits      = forms.DecimalField(max_digits=4, decimal_places=1, initial=3)
    subject_type = forms.ChoiceField(choices=SubjectType.choices, initial=SubjectType.CORE)
    department   = forms.ModelChoiceField(queryset=Department.objects.none(), required=False, empty_label="No department")
    status       = forms.ChoiceField(choices=SubjectStatus.choices, initial=SubjectStatus.ACTIVE)


class SubjectOfferingForm(forms.Form):
    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            from apps.accounts.models import TeacherProfile
            self.fields["academic_year"].queryset = AcademicYear.objects.filter(college=college).order_by("-start_date")
            self.fields["term"].queryset = Term.objects.filter(college=college).order_by("-start_date")
            self.fields["section"].queryset = (
                Section.objects.filter(college=college, status="active")
                .select_related("batch__program")
                .order_by("batch__name", "name")
            )
            self.fields["subject"].queryset = Subject.objects.filter(college=college, status="active").order_by("name")
            self.fields["teacher"].queryset = (
                TeacherProfile.objects.filter(college=college, status="active")
                .select_related("user")
                .order_by("user__first_name")
            )

    academic_year           = forms.ModelChoiceField(queryset=AcademicYear.objects.none(), empty_label="Select year")
    term                    = forms.ModelChoiceField(queryset=Term.objects.none(), empty_label="Select term")
    section                 = forms.ModelChoiceField(queryset=Section.objects.none(), empty_label="Select section")
    subject                 = forms.ModelChoiceField(queryset=Subject.objects.none(), empty_label="Select subject")
    teacher                 = forms.ModelChoiceField(queryset=None, required=False, empty_label="Unassigned")
    lecture_hours_per_week  = forms.DecimalField(max_digits=4, decimal_places=1, initial=3, required=False)
    room                    = forms.CharField(max_length=50, required=False)
    status                  = forms.ChoiceField(choices=SubjectOfferingStatus.choices, initial=SubjectOfferingStatus.ACTIVE)


class EnrollmentForm(forms.Form):
    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            from apps.accounts.models import StudentProfile
            self.fields["student"].queryset = (
                StudentProfile.objects.filter(college=college, status="active")
                .select_related("user")
                .order_by("user__first_name")
            )
            self.fields["academic_year"].queryset = AcademicYear.objects.filter(college=college).order_by("-start_date")
            self.fields["section"].queryset = (
                Section.objects.filter(college=college, status="active")
                .select_related("batch__program")
                .order_by("batch__name", "name")
            )

    student       = forms.ModelChoiceField(queryset=None, empty_label="Select student")
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.none(), empty_label="Select year")
    section       = forms.ModelChoiceField(queryset=Section.objects.none(), empty_label="Select section")
    roll_no       = forms.CharField(max_length=20, required=False, label="Roll number (optional)")
    status        = forms.ChoiceField(choices=EnrollmentStatus.choices, initial=EnrollmentStatus.ENROLLED)


class TimetableEntryForm(forms.Form):
    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            self.fields["subject_offering"].queryset = (
                SubjectOffering.objects.filter(college=college, status="active")
                .select_related("subject", "section__batch__program", "term")
                .order_by("section__batch__name", "subject__name")
            )

    subject_offering = forms.ModelChoiceField(queryset=SubjectOffering.objects.none(), empty_label="Select offering")
    day_of_week      = forms.ChoiceField(choices=DayOfWeek.choices)
    start_time       = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    end_time         = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    room             = forms.CharField(max_length=50, required=False)

    def clean(self):
        cleaned = super().clean()
        s, e = cleaned.get("start_time"), cleaned.get("end_time")
        if s and e and e <= s:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned
