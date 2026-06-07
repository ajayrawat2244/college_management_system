from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Avg, Count, Prefetch, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.accounts.models import StudentProfile, StudentStatus
from apps.academics.models import (
    Batch,
    Enrollment,
    Program,
    Section,
)
from apps.attendance.models import AttendanceRecord, AttendanceStatus
from apps.content.models import AssignmentSubmission
from apps.exams.models import ExamResult
from apps.finance.models import FeeInvoice, FeePayment, FeePaymentStatus


def _money(value):
    return value if value is not None else Decimal("0.00")


def build_student_queryset(college, params):
    search = (params.get("search") or "").strip()
    status = (params.get("status") or "").strip()
    program_id = (params.get("program") or "").strip()
    section_id = (params.get("section") or "").strip()
    batch_id = (params.get("batch") or "").strip()

    queryset = (
        StudentProfile.objects.filter(college=college)
        .select_related("user", "college", "photo_file_asset")
        .prefetch_related(
            Prefetch(
                "enrollments",
                queryset=Enrollment.objects.select_related(
                    "academic_year",
                    "section",
                    "section__batch",
                    "section__batch__program",
                ).order_by("-admission_date"),
            )
        )
        .order_by("user__first_name", "user__last_name", "admission_no")
    )

    if search:
        queryset = queryset.filter(
            Q(admission_no__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(user__email__icontains=search)
            | Q(user__phone__icontains=search)
        )

    if status:
        queryset = queryset.filter(status=status)

    if program_id:
        queryset = queryset.filter(enrollments__section__batch__program_id=program_id)

    if section_id:
        queryset = queryset.filter(enrollments__section_id=section_id)

    if batch_id:
        queryset = queryset.filter(enrollments__section__batch_id=batch_id)

    return queryset.distinct()


def build_student_filters(college):
    programs = (
        Program.objects.filter(college=college, status="active")
        .select_related("department")
        .order_by("name")
    )
    sections = (
        Section.objects.filter(college=college, status="active")
        .select_related("batch", "batch__program")
        .order_by("name")
    )
    batches = (
        Batch.objects.filter(college=college, status="active")
        .select_related("program", "academic_year")
        .order_by("-academic_year__start_date", "name")
    )

    return {
        "programs": programs,
        "sections": sections,
        "batches": batches,
        "student_status_choices": StudentStatus.choices,
    }


def paginate_students(queryset, page_number, per_page=12):
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(page_number)

    for student in page_obj.object_list:
        student.display_name = f"{student.user.first_name} {student.user.last_name or ''}".strip()
        enrollments = list(student.enrollments.all())
        student.latest_enrollment = enrollments[0] if enrollments else None

    return page_obj


def get_student_detail_context(college, student_id):
    student = get_object_or_404(
        StudentProfile.objects.filter(college=college)
        .select_related("user", "college", "photo_file_asset")
        .prefetch_related(
            Prefetch(
                "enrollments",
                queryset=Enrollment.objects.select_related(
                    "academic_year",
                    "section",
                    "section__batch",
                    "section__batch__program",
                ).order_by("-admission_date"),
            )
        ),
        pk=student_id,
    )
    student.display_name = f"{student.user.first_name} {student.user.last_name or ''}".strip()

    enrollments = list(student.enrollments.all())
    current_enrollment = enrollments[0] if enrollments else None

    attendance_qs = (
        AttendanceRecord.objects.filter(college=college, enrollment__student=student)
        .select_related(
            "attendance_session",
            "attendance_session__subject_offering",
            "attendance_session__subject_offering__subject",
        )
        .order_by("-marked_at")
    )
    attendance_summary = attendance_qs.aggregate(
        present=Count("id", filter=Q(attendance_status=AttendanceStatus.PRESENT)),
        absent=Count("id", filter=Q(attendance_status=AttendanceStatus.ABSENT)),
        late=Count("id", filter=Q(attendance_status=AttendanceStatus.LATE)),
        excused=Count("id", filter=Q(attendance_status=AttendanceStatus.EXCUSED)),
        total=Count("id"),
    )
    total_marked = attendance_summary["total"] or 0
    present = attendance_summary["present"] or 0
    attendance_percentage = round((present / total_marked) * 100, 2) if total_marked else 0

    fee_account = getattr(student, "fee_account", None)
    invoices_qs = FeeInvoice.objects.none()
    latest_payment = None
    fee_summary = {
        "invoice_count": 0,
        "total_amount": Decimal("0.00"),
        "paid_amount": Decimal("0.00"),
        "balance_amount": Decimal("0.00"),
    }
    if fee_account:
        invoices_qs = (
            fee_account.invoices.select_related("student_fee_account")
            .prefetch_related("items__fee_head", "payments")
            .order_by("-invoice_date")
        )
        fee_summary = invoices_qs.aggregate(
            invoice_count=Count("id"),
            total_amount=Sum("total_amount"),
            paid_amount=Sum("paid_amount"),
            balance_amount=Sum("balance_amount"),
        )
        latest_payment = (
            FeePayment.objects.filter(
                college=college,
                fee_invoice__student_fee_account__student=student,
                status=FeePaymentStatus.SUCCESSFUL,
            )
            .select_related("fee_invoice", "received_by")
            .order_by("-payment_date")
            .first()
        )

    exam_results_qs = (
        ExamResult.objects.filter(college=college, student=student)
        .select_related(
            "exam_paper",
            "exam_paper__exam",
            "exam_paper__subject_offering",
            "exam_paper__subject_offering__subject",
        )
        .order_by("-created_at")
    )
    exam_summary = exam_results_qs.aggregate(
        average_marks=Avg("marks_obtained"),
        result_count=Count("id"),
    )

    submissions_qs = (
        AssignmentSubmission.objects.filter(college=college, student=student)
        .select_related(
            "assignment",
            "assignment__subject_offering",
            "assignment__subject_offering__subject",
        )
        .order_by("-submitted_at", "-created_at")
    )
    submission_summary = submissions_qs.aggregate(
        total_submissions=Count("id"),
        graded_submissions=Count("id", filter=Q(marks_obtained__isnull=False)),
        pending_submissions=Count("id", filter=Q(marks_obtained__isnull=True)),
    )

    return {
        "student": student,
        "current_enrollment": current_enrollment,
        "attendance_summary": attendance_summary,
        "attendance_percentage": attendance_percentage,
        "recent_attendance": list(attendance_qs[:8]),
        "fee_account": fee_account,
        "fee_summary": {
            "invoice_count": fee_summary["invoice_count"] or 0,
            "total_amount": _money(fee_summary["total_amount"]),
            "paid_amount": _money(fee_summary["paid_amount"]),
            "balance_amount": _money(fee_summary["balance_amount"]),
        },
        "latest_payment": latest_payment,
        "recent_invoices": list(invoices_qs[:5]) if fee_account else [],
        "exam_summary": {
            "average_marks": _money(exam_summary["average_marks"]),
            "result_count": exam_summary["result_count"] or 0,
        },
        "recent_results": list(exam_results_qs[:5]),
        "assignment_summary": {
            "total_submissions": submission_summary["total_submissions"] or 0,
            "graded_submissions": submission_summary["graded_submissions"] or 0,
            "pending_submissions": submission_summary["pending_submissions"] or 0,
        },
        "recent_submissions": list(submissions_qs[:5]),
    }
