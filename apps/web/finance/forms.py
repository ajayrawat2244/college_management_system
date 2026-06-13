# apps/web/finance/forms.py
import uuid
from django import forms
from apps.finance.models import (
    FeeHeadCategory, FeeHeadStatus,
    FeeInvoiceStatus, FeePaymentStatus,
    FeeStructureStatus, PaymentMode,
)


class FeeHeadForm(forms.Form):
    code           = forms.CharField(max_length=50, widget=forms.TextInput(attrs={"placeholder": "e.g. TUITION"}))
    name           = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"placeholder": "e.g. Tuition Fee"}))
    category       = forms.ChoiceField(choices=FeeHeadCategory.choices)
    default_amount = forms.DecimalField(max_digits=12, decimal_places=2, initial=0)
    is_optional    = forms.BooleanField(required=False, label="Optional fee")
    status         = forms.ChoiceField(choices=FeeHeadStatus.choices, initial=FeeHeadStatus.ACTIVE)


class FeeStructureForm(forms.Form):
    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            from apps.academics.models import AcademicYear, Program, Section, Term
            self.fields["academic_year"].queryset = AcademicYear.objects.filter(
                college=college).order_by("-start_date")
            self.fields["program"].queryset = Program.objects.filter(
                college=college, status="active").order_by("name")
            self.fields["section"].queryset = (
                Section.objects.filter(college=college, status="active")
                .select_related("batch__program").order_by("batch__name", "name")
            )
            self.fields["term"].queryset = Term.objects.filter(
                college=college).order_by("-start_date")

    academic_year = forms.ModelChoiceField(queryset=None, empty_label="Select year")
    program       = forms.ModelChoiceField(queryset=None, empty_label="Select program")
    section       = forms.ModelChoiceField(queryset=None, required=False, empty_label="All sections")
    term          = forms.ModelChoiceField(queryset=None, required=False, empty_label="Full year (no term)")
    name          = forms.CharField(max_length=150, widget=forms.TextInput(attrs={"placeholder": "e.g. Annual Fee 2024-25"}))
    total_amount  = forms.DecimalField(max_digits=12, decimal_places=2, initial=0)
    status        = forms.ChoiceField(choices=FeeStructureStatus.choices, initial=FeeStructureStatus.ACTIVE)


class FeeInvoiceForm(forms.Form):
    """Issue a fee invoice for a student."""
    def __init__(self, *args, college=None, **kwargs):
        super().__init__(*args, **kwargs)
        if college:
            from apps.finance.models import StudentFeeAccount
            self.fields["student_fee_account"].queryset = (
                StudentFeeAccount.objects.filter(college=college, status="active")
                .select_related("student__user", "fee_structure")
                .order_by("student__user__first_name")
            )

    student_fee_account = forms.ModelChoiceField(queryset=None, empty_label="Select student account",
                                                  label="Student fee account")
    invoice_no          = forms.CharField(max_length=50,
                                          widget=forms.TextInput(attrs={"placeholder": "e.g. INV-2024-0001"}),
                                          required=False,
                                          help_text="Leave blank to auto-generate.")
    due_date            = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    total_amount        = forms.DecimalField(max_digits=12, decimal_places=2)
    notes               = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def clean_invoice_no(self):
        val = self.cleaned_data.get("invoice_no", "").strip()
        if not val:
            val = f"INV-{uuid.uuid4().hex[:8].upper()}"
        return val


class FeePaymentForm(forms.Form):
    """Record a payment against an invoice."""
    receipt_no   = forms.CharField(max_length=50,
                                   required=False,
                                   help_text="Leave blank to auto-generate.",
                                   widget=forms.TextInput(attrs={"placeholder": "e.g. REC-2024-0001"}))
    amount       = forms.DecimalField(max_digits=12, decimal_places=2, label="Amount (₹)")
    payment_mode = forms.ChoiceField(choices=PaymentMode.choices)
    reference_no = forms.CharField(max_length=100, required=False,
                                   label="Reference / UTR / Cheque no.",
                                   widget=forms.TextInput(attrs={"placeholder": "Optional"}))

    def clean_receipt_no(self):
        val = self.cleaned_data.get("receipt_no", "").strip()
        if not val:
            val = f"REC-{uuid.uuid4().hex[:8].upper()}"
        return val
