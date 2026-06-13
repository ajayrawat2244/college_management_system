# apps/web/content/forms.py
from django import forms
from apps.content.models import (
    AssignmentStatus, MaterialStatus, MaterialType,
    NoticeAudience, NoticeStatus, VisibilityScope,
)


class CourseMaterialForm(forms.Form):
    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            from apps.academics.models import SubjectOffering
            self.fields["subject_offering"].queryset = (
                SubjectOffering.objects.filter(college=college, status="active")
                .select_related("subject", "section__batch__program", "term")
                .order_by("section__batch__name", "subject__name")
            )

    subject_offering = forms.ModelChoiceField(
        queryset=None, empty_label="Select offering", required=False,
        label="Subject Offering (optional)",
    )
    title         = forms.CharField(max_length=255)
    material_type = forms.ChoiceField(choices=MaterialType.choices)
    description   = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))
    external_url  = forms.URLField(required=False, label="External URL (link/video)")
    file_upload   = forms.FileField(required=False, label="Upload file (PDF, doc, etc.)")
    visibility    = forms.ChoiceField(choices=VisibilityScope.choices, initial=VisibilityScope.STUDENTS)
    status        = forms.ChoiceField(
        choices=[(MaterialStatus.DRAFT, "Save as draft"), (MaterialStatus.PUBLISHED, "Publish now")],
        initial=MaterialStatus.DRAFT,
    )

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("external_url") and not cleaned.get("file_upload"):
            material_type = cleaned.get("material_type")
            if material_type not in (MaterialType.NOTE,):
                raise forms.ValidationError("Please provide either a file upload or an external URL.")
        return cleaned


class AssignmentForm(forms.Form):
    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            from apps.academics.models import SubjectOffering
            self.fields["subject_offering"].queryset = (
                SubjectOffering.objects.filter(college=college, status="active")
                .select_related("subject", "section__batch__program", "term")
                .order_by("section__batch__name", "subject__name")
            )

    subject_offering = forms.ModelChoiceField(
        queryset=None, empty_label="Select offering",
        label="Subject / Section",
    )
    title       = forms.CharField(max_length=255)
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4}))
    due_at      = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label="Due date/time",
    )
    max_marks   = forms.DecimalField(max_digits=8, decimal_places=2, initial=100, label="Max marks")
    file_upload = forms.FileField(required=False, label="Attachment (optional)")
    status      = forms.ChoiceField(
        choices=[(AssignmentStatus.DRAFT, "Save as draft"), (AssignmentStatus.PUBLISHED, "Publish now")],
        initial=AssignmentStatus.DRAFT,
    )


class AssignmentSubmissionForm(forms.Form):
    """Student submission form."""
    submission_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "Write your answer or notes here…"}),
        label="Submission text (optional)",
    )
    file_upload = forms.FileField(required=False, label="Attach file (optional)")

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("submission_text") and not cleaned.get("file_upload"):
            raise forms.ValidationError("Please provide either text or a file attachment.")
        return cleaned


class GradeSubmissionForm(forms.Form):
    """Teacher grades a single submission."""
    marks_obtained = forms.DecimalField(max_digits=8, decimal_places=2)
    feedback       = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))


class NoticeForm(forms.Form):
    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            from apps.academics.models import Section
            self.fields["target_section"].queryset = (
                Section.objects.filter(college=college, status="active")
                .select_related("batch__program")
                .order_by("batch__name", "name")
            )

    title          = forms.CharField(max_length=255)
    body           = forms.CharField(widget=forms.Textarea(attrs={"rows": 6}))
    audience_scope = forms.ChoiceField(choices=NoticeAudience.choices, initial=NoticeAudience.ALL)
    target_section = forms.ModelChoiceField(
        queryset=None, required=False, empty_label="All sections",
        label="Target section (if scope = Section)",
    )
    priority = forms.IntegerField(initial=0, min_value=0, max_value=10,
                                  help_text="Higher = more prominent (0–10)")
    publish_at  = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label="Schedule publish (optional)",
    )
    expires_at  = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        label="Expires at (optional)",
    )
    status = forms.ChoiceField(
        choices=[(NoticeStatus.DRAFT, "Save as draft"), (NoticeStatus.PUBLISHED, "Publish now")],
        initial=NoticeStatus.DRAFT,
    )
    file_upload = forms.FileField(required=False, label="Attachment (optional)")
