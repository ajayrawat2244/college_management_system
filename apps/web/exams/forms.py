# apps/web/exams/forms.py
from django import forms
from apps.exams.models import (
    ExamStatus, ExamPaperStatus, ExamResultStatus, GradeScaleStatus,
)


class GradingScaleForm(forms.Form):
    grade_label     = forms.CharField(max_length=10, widget=forms.TextInput(attrs={"placeholder": "e.g. A+"}))
    min_percentage  = forms.DecimalField(max_digits=5, decimal_places=2, label="Min %")
    max_percentage  = forms.DecimalField(max_digits=5, decimal_places=2, label="Max %")
    grade_point     = forms.DecimalField(max_digits=4, decimal_places=2, required=False, label="Grade point (optional)")
    remarks         = forms.CharField(required=False, widget=forms.TextInput(attrs={"placeholder": "e.g. Excellent"}))
    effective_from  = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    effective_to    = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    status          = forms.ChoiceField(choices=GradeScaleStatus.choices, initial=GradeScaleStatus.ACTIVE)

    def clean(self):
        cleaned = super().clean()
        mn, mx = cleaned.get("min_percentage"), cleaned.get("max_percentage")
        if mn is not None and mx is not None and mx <= mn:
            raise forms.ValidationError("Max % must be greater than Min %.")
        return cleaned


class ExamForm(forms.Form):
    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            from apps.academics.models import AcademicYear, Section, Term
            self.fields["academic_year"].queryset = AcademicYear.objects.filter(
                college=college).order_by("-start_date")
            self.fields["term"].queryset = Term.objects.filter(
                college=college).order_by("-start_date")
            self.fields["section"].queryset = (
                Section.objects.filter(college=college, status="active")
                .select_related("batch__program").order_by("batch__name", "name")
            )

    academic_year = forms.ModelChoiceField(queryset=None, empty_label="Select year")
    term          = forms.ModelChoiceField(queryset=None, required=False, empty_label="All terms")
    section       = forms.ModelChoiceField(queryset=None, empty_label="Select section")
    name          = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"placeholder": "e.g. Mid-Term Examination 2024"}))
    exam_type     = forms.ChoiceField(choices=[
        ("unit", "Unit Test"), ("quiz", "Quiz"), ("midterm", "Midterm"),
        ("final", "Final Exam"), ("practical", "Practical"), ("other", "Other"),
    ])
    start_date    = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    end_date      = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    status        = forms.ChoiceField(choices=ExamStatus.choices, initial=ExamStatus.DRAFT)

    def clean(self):
        cleaned = super().clean()
        s, e = cleaned.get("start_date"), cleaned.get("end_date")
        if s and e and e < s:
            raise forms.ValidationError("End date cannot be before start date.")
        return cleaned


class ExamPaperForm(forms.Form):
    def __init__(self, *args, college=None, exam=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            from apps.academics.models import SubjectOffering
            qs = SubjectOffering.objects.filter(college=college, status="active").select_related(
                "subject", "section__batch__program", "term")
            if exam:
                qs = qs.filter(section=exam.section)
            self.fields["subject_offering"].queryset = qs.order_by("subject__name")

    subject_offering = forms.ModelChoiceField(queryset=None, empty_label="Select subject")
    exam_date        = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    start_time       = forms.TimeField(required=False, widget=forms.TimeInput(attrs={"type": "time"}))
    end_time         = forms.TimeField(required=False, widget=forms.TimeInput(attrs={"type": "time"}))
    max_marks        = forms.DecimalField(max_digits=8, decimal_places=2, initial=100)
    pass_marks       = forms.DecimalField(max_digits=8, decimal_places=2, required=False)
    room             = forms.CharField(max_length=50, required=False)
    status           = forms.ChoiceField(choices=ExamPaperStatus.choices, initial=ExamPaperStatus.SCHEDULED)


class BulkResultEntryForm(forms.Form):
    """Dynamically built per-student in the view; this is the session-level wrapper."""
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))
