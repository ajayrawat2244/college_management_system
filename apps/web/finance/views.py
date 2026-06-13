# apps/web/finance/views.py
"""
Web views for the Finance module.

Covered:
  FeeHead         — list, create (admin)
  FeeStructure    — list, create, detail (admin)
  StudentFeeAccount — list (admin), detail
  FeeInvoice      — list, create, detail, record payment (admin)
  Student         — view own invoices and payments
  Finance summary — admin overview with KPIs
"""
import logging
from decimal import Decimal

from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from apps.finance.models import (
    FeeHead, FeeInvoice, FeeInvoiceStatus,
    FeePayment, FeePaymentStatus,
    FeeStructure, FeeStructureItem,
    StudentFeeAccount,
)
from apps.web.finance.forms import (
    FeeHeadForm, FeeInvoiceForm, FeePaymentForm, FeeStructureForm,
)
from apps.web.mixins import CollegeAdminRequiredMixin, StudentRequiredMixin

logger = logging.getLogger(__name__)


def _college(r):
    return r.college


# ══════════════════════════════════════════════════════════════
# FEE HEADS
# ══════════════════════════════════════════════════════════════

class FeeHeadListView(CollegeAdminRequiredMixin, View):
    template_name = "web/finance/fee_heads/list.html"

    def get(self, request):
        heads = FeeHead.objects.filter(college=_college(request)).order_by("category", "name")
        return render(request, self.template_name, {
            "page_title": "Fee Heads",
            "fee_heads": heads,
            "form": FeeHeadForm(),
        })

    def post(self, request):
        college = _college(request)
        form = FeeHeadForm(request.POST)
        if not form.is_valid():
            heads = FeeHead.objects.filter(college=college).order_by("category", "name")
            return render(request, self.template_name, {
                "page_title": "Fee Heads", "fee_heads": heads, "form": form,
            })
        cd = form.cleaned_data
        try:
            FeeHead.objects.create(
                college=college,
                code=cd["code"].upper(),
                name=cd["name"],
                category=cd["category"],
                default_amount=cd["default_amount"],
                is_optional=cd.get("is_optional", False),
                status=cd["status"],
            )
            messages.success(request, f"Fee head '{cd['name']}' created.")
        except IntegrityError:
            form.add_error("code", "A fee head with this code already exists.")
            heads = FeeHead.objects.filter(college=college).order_by("category", "name")
            return render(request, self.template_name, {
                "page_title": "Fee Heads", "fee_heads": heads, "form": form,
            })
        return redirect("web:fee_head_list")


# ══════════════════════════════════════════════════════════════
# FEE STRUCTURES
# ══════════════════════════════════════════════════════════════

class FeeStructureListView(CollegeAdminRequiredMixin, View):
    template_name = "web/finance/fee_structures/list.html"

    def get(self, request):
        structures = (
            FeeStructure.objects.filter(college=_college(request))
            .select_related("academic_year", "program", "section", "term")
            .order_by("-academic_year__start_date", "program__name")
        )
        return render(request, self.template_name, {
            "page_title": "Fee Structures", "structures": structures,
        })


class FeeStructureCreateView(CollegeAdminRequiredMixin, View):
    template_name = "web/finance/fee_structures/form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "page_title": "Create Fee Structure",
            "form": FeeStructureForm(college=_college(request)),
        })

    def post(self, request):
        college = _college(request)
        form = FeeStructureForm(request.POST, college=college)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Create Fee Structure", "form": form})
        cd = form.cleaned_data
        try:
            FeeStructure.objects.create(
                college=college,
                academic_year=cd["academic_year"],
                program=cd["program"],
                section=cd.get("section"),
                term=cd.get("term"),
                name=cd["name"],
                total_amount=cd["total_amount"],
                status=cd["status"],
            )
            messages.success(request, f"Fee structure '{cd['name']}' created.")
            return redirect("web:fee_structure_list")
        except IntegrityError:
            form.add_error(None, "A fee structure with this combination already exists.")
            return render(request, self.template_name, {"page_title": "Create Fee Structure", "form": form})


class FeeStructureDetailView(CollegeAdminRequiredMixin, View):
    template_name = "web/finance/fee_structures/detail.html"

    def get(self, request, structure_id):
        college = _college(request)
        structure = get_object_or_404(FeeStructure, id=structure_id, college=college)
        items = structure.items.select_related("fee_head").order_by("sort_order")
        accounts = (
            StudentFeeAccount.objects.filter(fee_structure=structure)
            .select_related("student__user")
            .count()
        )
        return render(request, self.template_name, {
            "page_title": structure.name,
            "structure": structure,
            "items": items,
            "account_count": accounts,
        })


# ══════════════════════════════════════════════════════════════
# STUDENT FEE ACCOUNTS
# ══════════════════════════════════════════════════════════════

class StudentFeeAccountListView(CollegeAdminRequiredMixin, View):
    template_name = "web/finance/invoices/account_list.html"

    def get(self, request):
        college = _college(request)
        accounts = (
            StudentFeeAccount.objects.filter(college=college)
            .select_related("student__user", "fee_structure")
            .order_by("student__user__first_name")
        )
        return render(request, self.template_name, {
            "page_title": "Student Fee Accounts",
            "accounts": accounts,
        })


# ══════════════════════════════════════════════════════════════
# FEE INVOICES
# ══════════════════════════════════════════════════════════════

class FeeInvoiceListView(CollegeAdminRequiredMixin, View):
    template_name = "web/finance/invoices/list.html"

    def get(self, request):
        college = _college(request)
        invoices = (
            FeeInvoice.objects.filter(college=college)
            .select_related("student_fee_account__student__user")
            .order_by("-created_at")
        )
        # KPIs
        totals = invoices.aggregate(
            total_issued=Sum("total_amount"),
            total_paid=Sum("paid_amount"),
        )
        pending_count = invoices.filter(
            status__in=[FeeInvoiceStatus.ISSUED, FeeInvoiceStatus.PART_PAID, FeeInvoiceStatus.OVERDUE]
        ).count()
        return render(request, self.template_name, {
            "page_title": "Fee Invoices",
            "invoices": invoices[:200],
            "total_issued": totals["total_issued"] or 0,
            "total_paid": totals["total_paid"] or 0,
            "pending_count": pending_count,
        })


class FeeInvoiceCreateView(CollegeAdminRequiredMixin, View):
    template_name = "web/finance/invoices/form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "page_title": "Issue Invoice",
            "form": FeeInvoiceForm(college=_college(request)),
        })

    def post(self, request):
        college = _college(request)
        form = FeeInvoiceForm(request.POST, college=college)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Issue Invoice", "form": form})
        cd = form.cleaned_data
        total = cd["total_amount"]
        try:
            invoice = FeeInvoice.objects.create(
                college=college,
                student_fee_account=cd["student_fee_account"],
                invoice_no=cd["invoice_no"],
                due_date=cd.get("due_date"),
                total_amount=total,
                paid_amount=Decimal("0"),
                balance_amount=total,
                issued_by=request.user,
                notes=cd.get("notes", ""),
                status=FeeInvoiceStatus.ISSUED,
            )
            messages.success(request, f"Invoice {invoice.invoice_no} issued.")
            return redirect("web:invoice_detail", invoice_id=invoice.id)
        except IntegrityError:
            form.add_error("invoice_no", "An invoice with this number already exists.")
            return render(request, self.template_name, {"page_title": "Issue Invoice", "form": form})


class FeeInvoiceDetailView(CollegeAdminRequiredMixin, View):
    template_name = "web/finance/invoices/detail.html"

    def get(self, request, invoice_id):
        college = _college(request)
        invoice = get_object_or_404(FeeInvoice, id=invoice_id, college=college)
        items = invoice.items.select_related("fee_head").order_by("fee_head__name")
        payments = invoice.payments.order_by("-payment_date")
        return render(request, self.template_name, {
            "page_title": f"Invoice {invoice.invoice_no}",
            "invoice": invoice,
            "items": items,
            "payments": payments,
            "payment_form": FeePaymentForm(),
        })


class RecordPaymentView(CollegeAdminRequiredMixin, View):
    """POST only — record a payment against an invoice."""

    def post(self, request, invoice_id):
        college = _college(request)
        invoice = get_object_or_404(FeeInvoice, id=invoice_id, college=college)

        if invoice.status in (FeeInvoiceStatus.PAID, FeeInvoiceStatus.VOID):
            messages.error(request, "Cannot record payment for a paid or void invoice.")
            return redirect("web:invoice_detail", invoice_id=invoice_id)

        form = FeePaymentForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Invalid payment data. Please check and try again.")
            return redirect("web:invoice_detail", invoice_id=invoice_id)

        cd = form.cleaned_data
        amount = cd["amount"]

        with transaction.atomic():
            try:
                FeePayment.objects.create(
                    college=college,
                    fee_invoice=invoice,
                    receipt_no=cd["receipt_no"],
                    amount=amount,
                    payment_mode=cd["payment_mode"],
                    reference_no=cd.get("reference_no", ""),
                    received_by=request.user,
                    status=FeePaymentStatus.SUCCESSFUL,
                )
            except IntegrityError:
                messages.error(request, "Receipt number already exists.")
                return redirect("web:invoice_detail", invoice_id=invoice_id)

            # Update invoice paid/balance amounts and status
            invoice.paid_amount = (invoice.paid_amount or Decimal("0")) + amount
            invoice.balance_amount = max(Decimal("0"), invoice.total_amount - invoice.paid_amount)
            if invoice.balance_amount == 0:
                invoice.status = FeeInvoiceStatus.PAID
            elif invoice.paid_amount > 0:
                invoice.status = FeeInvoiceStatus.PART_PAID
            invoice.save(update_fields=["paid_amount", "balance_amount", "status"])

        messages.success(request, f"Payment of ₹{amount} recorded (Receipt: {cd['receipt_no']}).")
        return redirect("web:invoice_detail", invoice_id=invoice.id)


# ══════════════════════════════════════════════════════════════
# STUDENT — MY FEES
# ══════════════════════════════════════════════════════════════

class StudentFeeView(StudentRequiredMixin, View):
    template_name = "web/finance/invoices/student.html"

    def get(self, request):
        college = _college(request)
        try:
            student = request.user.student_profile
            account = StudentFeeAccount.objects.filter(student=student, college=college).first()
        except Exception:
            account = None

        invoices, payments = [], []
        if account:
            invoices = account.invoices.order_by("-created_at")
            payments = FeePayment.objects.filter(
                fee_invoice__in=invoices,
                status=FeePaymentStatus.SUCCESSFUL,
            ).select_related("fee_invoice").order_by("-payment_date")

        total_dues = sum(inv.balance_amount for inv in invoices if inv.status not in (
            FeeInvoiceStatus.PAID, FeeInvoiceStatus.VOID))

        return render(request, self.template_name, {
            "page_title": "My Fees",
            "account": account,
            "invoices": invoices,
            "payments": payments,
            "total_dues": total_dues,
        })


# ══════════════════════════════════════════════════════════════
# FINANCE OVERVIEW (admin summary dashboard)
# ══════════════════════════════════════════════════════════════

class FinanceOverviewView(CollegeAdminRequiredMixin, View):
    template_name = "web/finance/invoices/overview.html"

    def get(self, request):
        college = _college(request)
        invoices = FeeInvoice.objects.filter(college=college)
        totals = invoices.aggregate(
            total_issued=Sum("total_amount"),
            total_paid=Sum("paid_amount"),
            total_balance=Sum("balance_amount"),
        )
        status_breakdown = {
            "issued":    invoices.filter(status=FeeInvoiceStatus.ISSUED).count(),
            "part_paid": invoices.filter(status=FeeInvoiceStatus.PART_PAID).count(),
            "paid":      invoices.filter(status=FeeInvoiceStatus.PAID).count(),
            "overdue":   invoices.filter(status=FeeInvoiceStatus.OVERDUE).count(),
            "void":      invoices.filter(status=FeeInvoiceStatus.VOID).count(),
        }
        recent_payments = (
            FeePayment.objects.filter(college=college, status=FeePaymentStatus.SUCCESSFUL)
            .select_related("fee_invoice__student_fee_account__student__user")
            .order_by("-payment_date")[:10]
        )
        return render(request, self.template_name, {
            "page_title": "Finance Overview",
            "totals": totals,
            "status_breakdown": status_breakdown,
            "recent_payments": recent_payments,
            "total_accounts": StudentFeeAccount.objects.filter(college=college).count(),
        })
