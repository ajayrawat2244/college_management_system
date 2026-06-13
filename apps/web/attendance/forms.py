# apps/web/attendance/forms.py
from django import forms
from apps.attendance.models import AttendanceStatus, AttendanceSessionStatus


class AttendanceSessionForm(forms.Form):
    """Open a new attendance session for a subject offering."""

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
    session_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    start_time   = forms.TimeField(required=False, widget=forms.TimeInput(attrs={"type": "time"}))
    end_time     = forms.TimeField(required=False, widget=forms.TimeInput(attrs={"type": "time"}))
    notes        = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))


class BulkAttendanceForm(forms.Form):
    """
    Dynamically built in the view — each enrollment gets one field.
    This base form is used for the session-level notes/status only.
    """
    notes  = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))
    status = forms.ChoiceField(
        choices=AttendanceSessionStatus.choices,
        initial=AttendanceSessionStatus.CLOSED,
        label="Close session after saving",
    )
