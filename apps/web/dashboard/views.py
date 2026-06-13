# apps/web/dashboard/views.py
"""
Dashboard views — one per role, all real DB aggregations.
"""
import logging

from django.db.models import Count, Q, Sum
from django.shortcuts import redirect, render
from django.views import View

from apps.web.mixins import (
    CollegeAdminRequiredMixin,
    LoginRequiredMixin,
    StudentRequiredMixin,
    TeacherRequiredMixin,
    TenantRequiredMixin,
)

logger = logging.getLogger(__name__)


class DashboardView(LoginRequiredMixin, TenantRequiredMixin, View):
    """Generic fallback dashboard for users with no specific role yet."""
    login_url = "web:login"
    template_name = "web/dashboard/dashboard.html"

    def get(self, request):
        return render(request, self.template_name, {
            "page_title": "Dashboard",
            "page_subtitle": request.college.name,
        })


class AdminDashboardView(CollegeAdminRequiredMixin, View):
    template_name = "web/dashboard/admin_dashboard.html"

    def get(self, request):
        college = request.college

        # ── Students ──────────────────────────────────────
        from apps.accounts.models import StudentProfile
        students_qs = StudentProfile.objects.filter(college=college)
        total_students  = students_qs.count()
        active_students = students_qs.filter(status="active").count()

        # ── Teachers ──────────────────────────────────────
        from apps.accounts.models import TeacherProfile
        total_teachers = TeacherProfile.objects.filter(college=college).count()

        # ── Programs / Batches ────────────────────────────
        from apps.academics.models import Batch, Program
        total_programs = Program.objects.filter(college=college, status="active").count()
        total_batches  = Batch.objects.filter(college=college, status="active").count()

        # ── Finance ───────────────────────────────────────
        total_fee_collected = 0
        pending_fees        = 0
        try:
            from apps.finance.models import FeeInvoice, FeeInvoiceStatus, FeePayment, FeePaymentStatus
            total_fee_collected = (
                FeePayment.objects.filter(college=college, status=FeePaymentStatus.SUCCESSFUL)
                .aggregate(t=Sum("amount"))["t"] or 0
            )
            pending_fees = FeeInvoice.objects.filter(
                college=college,
                status__in=[FeeInvoiceStatus.ISSUED, FeeInvoiceStatus.PART_PAID, FeeInvoiceStatus.OVERDUE],
            ).count()
        except Exception as exc:
            logger.warning("Finance KPI error: %s", exc)

        # ── Exams ─────────────────────────────────────────
        total_exams = 0
        exams_with_results_declared = 0
        try:
            from apps.exams.models import Exam, ExamStatus
            total_exams = Exam.objects.filter(college=college).count()
            exams_with_results_declared = Exam.objects.filter(
                college=college, status=ExamStatus.RESULT_DECLARED
            ).count()
        except Exception as exc:
            logger.warning("Exams KPI error: %s", exc)

        # ── Recent students ───────────────────────────────
        recent_students = (
            students_qs.select_related("user")
            .order_by("-created_at")[:8]
        )

        return render(request, self.template_name, {
            "page_title":    "Dashboard",
            "page_subtitle": f"{college.name} · Admin Overview",
            "total_students":              total_students,
            "active_students":             active_students,
            "total_teachers":              total_teachers,
            "total_programs":              total_programs,
            "total_batches":               total_batches,
            "total_fee_collected":         total_fee_collected,
            "pending_fees":                pending_fees,
            "total_exams":                 total_exams,
            "exams_with_results_declared": exams_with_results_declared,
            "recent_students":             recent_students,
        })


class TeacherDashboardView(TeacherRequiredMixin, View):
    template_name = "web/dashboard/teacher_dashboard.html"

    def get(self, request):
        college = request.college
        try:
            teacher = request.user.teacher_profile
        except Exception:
            teacher = None

        from apps.academics.models import SubjectOffering, Term
        current_term = Term.objects.filter(college=college, is_current=True).first()

        my_offerings = []
        if teacher and current_term:
            my_offerings = (
                SubjectOffering.objects.filter(
                    college=college, teacher=teacher, term=current_term, status="active"
                ).select_related("subject", "section__batch__program")[:10]
            )

        from apps.academics.models import Enrollment
        my_student_count = 0
        if my_offerings:
            section_ids = [o.section_id for o in my_offerings]
            my_student_count = (
                Enrollment.objects.filter(
                    college=college, section__in=section_ids, status="enrolled"
                ).values("student").distinct().count()
            )

        return render(request, self.template_name, {
            "page_title":       "Teacher Dashboard",
            "page_subtitle":    f"{college.name} · My Classes",
            "teacher":          teacher,
            "current_term":     current_term,
            "my_offerings":     my_offerings,
            "my_student_count": my_student_count,
        })


class StudentDashboardView(StudentRequiredMixin, View):
    template_name = "web/dashboard/student_dashboard.html"

    def get(self, request):
        college = request.college
        try:
            student = request.user.student_profile
        except Exception:
            student = None

        from apps.academics.models import Enrollment, SubjectOffering, Term
        current_term   = Term.objects.filter(college=college, is_current=True).first()
        current_enroll = None
        my_subjects    = []
        pending_fee_count = 0

        if student:
            current_enroll = (
                Enrollment.objects.filter(college=college, student=student, status="enrolled")
                .select_related("section__batch__program", "academic_year")
                .first()
            )
            if current_enroll and current_term:
                my_subjects = (
                    SubjectOffering.objects.filter(
                        college=college,
                        section=current_enroll.section,
                        term=current_term,
                        status="active",
                    ).select_related("subject", "teacher__user")[:8]
                )
            try:
                from apps.finance.models import FeeInvoice, FeeInvoiceStatus
                pending_fee_count = FeeInvoice.objects.filter(
                    college=college,
                    student_fee_account__student=student,
                    status__in=[FeeInvoiceStatus.ISSUED, FeeInvoiceStatus.PART_PAID, FeeInvoiceStatus.OVERDUE],
                ).count()
            except Exception:
                pass

        return render(request, self.template_name, {
            "page_title":       "My Dashboard",
            "page_subtitle":    college.name,
            "student":          student,
            "current_term":     current_term,
            "current_enroll":   current_enroll,
            "my_subjects":      my_subjects,
            "pending_fee_count": pending_fee_count,
        })


class RootRedirectView(View):
    def get(self, request):
        if request.user.is_authenticated:
            from apps.web.utils import get_post_login_redirect
            return redirect(get_post_login_redirect(request.user, getattr(request, "college", None)))
        return redirect("web:login")


class NoTenantView(View):
    def get(self, request):
        return render(request, "web/errors/no_tenant.html", status=404)


class SubscriptionRequiredView(View):
    def get(self, request):
        return render(request, "web/errors/subscription_required.html", status=403)


class ForbiddenView(View):
    def get(self, request):
        return render(request, "web/errors/403.html", status=403)
