# apps/web/exams/views.py
"""
Web views for the Exams module.

Covered:
  GradingScale   — list, create (admin)
  Exam           — list, create, detail (admin/teacher)
  ExamPaper      — add papers to an exam (admin/teacher)
  ExamResult     — bulk enter marks per paper (teacher), publish (admin)
  Student        — view own results
"""
import logging
from django.contrib import messages
from django.db import IntegrityError
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from apps.exams.models import (
    Exam, ExamPaper, ExamResult, ExamResultStatus,
    ExamStatus, GradingScale,
)
from apps.web.exams.forms import ExamForm, ExamPaperForm, GradingScaleForm
from apps.web.mixins import (
    CollegeAdminRequiredMixin, StudentRequiredMixin, TeacherRequiredMixin,
)
from apps.platforms.permissions import ROLE_COLLEGE_ADMIN, _has_role

logger = logging.getLogger(__name__)


def _college(r):
    return r.college


# ══════════════════════════════════════════════════════════════
# GRADING SCALE
# ══════════════════════════════════════════════════════════════

class GradingScaleListView(CollegeAdminRequiredMixin, View):
    template_name = "web/exams/grading/list.html"

    def get(self, request):
        scales = GradingScale.objects.filter(college=_college(request)).order_by("-min_percentage")
        return render(request, self.template_name, {
            "page_title": "Grading Scale",
            "scales": scales,
            "form": GradingScaleForm(),
        })

    def post(self, request):
        college = _college(request)
        form = GradingScaleForm(request.POST)
        if not form.is_valid():
            scales = GradingScale.objects.filter(college=college).order_by("-min_percentage")
            return render(request, self.template_name, {
                "page_title": "Grading Scale", "scales": scales, "form": form,
            })
        cd = form.cleaned_data
        try:
            GradingScale.objects.create(
                college=college,
                grade_label=cd["grade_label"].upper(),
                min_percentage=cd["min_percentage"],
                max_percentage=cd["max_percentage"],
                grade_point=cd.get("grade_point"),
                remarks=cd.get("remarks", ""),
                effective_from=cd.get("effective_from"),
                effective_to=cd.get("effective_to"),
                status=cd["status"],
            )
            messages.success(request, f"Grade '{cd['grade_label'].upper()}' added.")
        except IntegrityError:
            form.add_error("grade_label", "This grade label already exists.")
            scales = GradingScale.objects.filter(college=college).order_by("-min_percentage")
            return render(request, self.template_name, {
                "page_title": "Grading Scale", "scales": scales, "form": form,
            })
        return redirect("web:grading_scale_list")


# ══════════════════════════════════════════════════════════════
# EXAMS
# ══════════════════════════════════════════════════════════════

class ExamListView(TeacherRequiredMixin, View):
    template_name = "web/exams/exams/list.html"

    def get(self, request):
        college = _college(request)
        exams = (
            Exam.objects.filter(college=college)
            .select_related("academic_year", "term", "section__batch__program")
            .annotate(paper_count=Count("papers"))
            .order_by("-created_at")
        )
        return render(request, self.template_name, {
            "page_title": "Exams", "exams": exams,
        })


class ExamCreateView(CollegeAdminRequiredMixin, View):
    template_name = "web/exams/exams/form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "page_title": "Create Exam",
            "form": ExamForm(college=_college(request)),
        })

    def post(self, request):
        college = _college(request)
        form = ExamForm(request.POST, college=college)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Create Exam", "form": form})
        cd = form.cleaned_data
        exam = Exam.objects.create(
            college=college,
            academic_year=cd["academic_year"],
            term=cd.get("term"),
            section=cd["section"],
            name=cd["name"],
            exam_type=cd["exam_type"],
            start_date=cd.get("start_date"),
            end_date=cd.get("end_date"),
            status=cd["status"],
        )
        messages.success(request, f"Exam '{exam.name}' created.")
        return redirect("web:exam_detail", exam_id=exam.id)


class ExamDetailView(TeacherRequiredMixin, View):
    template_name = "web/exams/exams/detail.html"

    def get(self, request, exam_id):
        college = _college(request)
        exam = get_object_or_404(Exam, id=exam_id, college=college)
        papers = (
            exam.papers.select_related("subject_offering__subject", "subject_offering__teacher__user")
            .order_by("exam_date", "start_time")
        )
        return render(request, self.template_name, {
            "page_title": exam.name,
            "exam": exam,
            "papers": papers,
            "is_admin": _has_role(request.user, college, ROLE_COLLEGE_ADMIN) or request.user.is_superuser,
        })

    def post(self, request, exam_id):
        """Change exam status (schedule / conduct / declare / archive)."""
        college = _college(request)
        if not _has_role(request.user, college, ROLE_COLLEGE_ADMIN) and not request.user.is_superuser:
            messages.error(request, "Permission denied.")
            return redirect("web:exam_detail", exam_id=exam_id)
        exam = get_object_or_404(Exam, id=exam_id, college=college)
        action = request.POST.get("action")
        status_map = {
            "schedule": ExamStatus.SCHEDULED,
            "conduct":  ExamStatus.CONDUCTED,
            "declare":  ExamStatus.RESULT_DECLARED,
            "archive":  ExamStatus.ARCHIVED,
        }
        if action in status_map:
            exam.status = status_map[action]
            exam.save(update_fields=["status"])
            messages.success(request, f"Exam marked as {exam.get_status_display()}.")
        return redirect("web:exam_detail", exam_id=exam.id)


# ══════════════════════════════════════════════════════════════
# EXAM PAPERS
# ══════════════════════════════════════════════════════════════

class ExamPaperCreateView(CollegeAdminRequiredMixin, View):
    template_name = "web/exams/papers/form.html"

    def get(self, request, exam_id):
        college = _college(request)
        exam = get_object_or_404(Exam, id=exam_id, college=college)
        return render(request, self.template_name, {
            "page_title": "Add Exam Paper",
            "exam": exam,
            "form": ExamPaperForm(college=college, exam=exam),
        })

    def post(self, request, exam_id):
        college = _college(request)
        exam = get_object_or_404(Exam, id=exam_id, college=college)
        form = ExamPaperForm(request.POST, college=college, exam=exam)
        if not form.is_valid():
            return render(request, self.template_name, {
                "page_title": "Add Exam Paper", "exam": exam, "form": form,
            })
        cd = form.cleaned_data
        try:
            ExamPaper.objects.create(
                college=college,
                exam=exam,
                subject_offering=cd["subject_offering"],
                exam_date=cd.get("exam_date"),
                start_time=cd.get("start_time"),
                end_time=cd.get("end_time"),
                max_marks=cd["max_marks"],
                pass_marks=cd.get("pass_marks"),
                room=cd.get("room", ""),
                status=cd["status"],
            )
            messages.success(request, "Exam paper added.")
        except IntegrityError:
            form.add_error("subject_offering", "A paper for this subject already exists in this exam.")
            return render(request, self.template_name, {
                "page_title": "Add Exam Paper", "exam": exam, "form": form,
            })
        return redirect("web:exam_detail", exam_id=exam.id)


# ══════════════════════════════════════════════════════════════
# EXAM RESULTS — BULK ENTRY (teacher / admin)
# ══════════════════════════════════════════════════════════════

class ExamResultEntryView(TeacherRequiredMixin, View):
    """Enter / edit marks for all students for a given ExamPaper."""
    template_name = "web/exams/results/entry.html"

    def _get_students_and_results(self, paper, college):
        from apps.academics.models import Enrollment
        enrollments = (
            Enrollment.objects.filter(
                section=paper.exam.section, college=college, status="enrolled"
            ).select_related("student__user").order_by("roll_no", "student__user__first_name")
        )
        existing = {
            str(r.student_id): r
            for r in ExamResult.objects.filter(exam_paper=paper)
        }
        rows = []
        for enroll in enrollments:
            result = existing.get(str(enroll.student_id))
            rows.append({
                "enrollment": enroll,
                "result": result,
                "marks": result.marks_obtained if result else "",
                "remarks": result.remarks if result else "",
            })
        return rows

    def get(self, request, paper_id):
        college = _college(request)
        paper = get_object_or_404(ExamPaper, id=paper_id, college=college)
        rows = self._get_students_and_results(paper, college)
        grading_scales = GradingScale.objects.filter(college=college, status="active").order_by("-min_percentage")
        return render(request, self.template_name, {
            "page_title": f"Enter Results — {paper.subject_offering.subject.name}",
            "paper": paper,
            "rows": rows,
            "grading_scales": grading_scales,
        })

    def post(self, request, paper_id):
        college = _college(request)
        paper = get_object_or_404(ExamPaper, id=paper_id, college=college)
        from apps.academics.models import Enrollment
        enrollments = Enrollment.objects.filter(
            section=paper.exam.section, college=college, status="enrolled"
        ).select_related("student")

        grading_scales = list(
            GradingScale.objects.filter(college=college, status="active").order_by("-min_percentage")
        )
        saved = 0
        for enroll in enrollments:
            raw = request.POST.get(f"marks_{enroll.student_id}", "").strip()
            if not raw:
                continue
            try:
                marks = float(raw)
            except ValueError:
                continue

            # Auto-assign grade from scale
            grade_label, grade_point = "", None
            for scale in grading_scales:
                pct = (marks / float(paper.max_marks)) * 100
                if float(scale.min_percentage) <= pct <= float(scale.max_percentage):
                    grade_label = scale.grade_label
                    grade_point = scale.grade_point
                    break

            ExamResult.objects.update_or_create(
                exam_paper=paper,
                student=enroll.student,
                defaults={
                    "college": college,
                    "marks_obtained": marks,
                    "grade_label": grade_label,
                    "grade_point": grade_point,
                    "remarks": request.POST.get(f"remarks_{enroll.student_id}", ""),
                    "evaluated_by": request.user,
                    "evaluated_at": timezone.now(),
                    "status": ExamResultStatus.DRAFT,
                },
            )
            saved += 1

        # Publish if requested
        if request.POST.get("publish_results"):
            ExamResult.objects.filter(exam_paper=paper).update(status=ExamResultStatus.PUBLISHED)
            messages.success(request, f"Results published for {saved} students.")
        else:
            messages.success(request, f"Results saved for {saved} students.")
        return redirect("web:exam_detail", exam_id=paper.exam_id)


class ExamResultDetailView(TeacherRequiredMixin, View):
    """View all results for a single ExamPaper with stats."""
    template_name = "web/exams/results/detail.html"

    def get(self, request, paper_id):
        college = _college(request)
        paper = get_object_or_404(ExamPaper, id=paper_id, college=college)
        results = (
            ExamResult.objects.filter(exam_paper=paper)
            .select_related("student__user")
            .order_by("student__user__first_name")
        )
        stats = results.aggregate(
            avg=Avg("marks_obtained"),
            total=Count("id"),
        )
        pass_count = 0
        if paper.pass_marks:
            pass_count = results.filter(marks_obtained__gte=paper.pass_marks).count()
        return render(request, self.template_name, {
            "page_title": f"Results — {paper.subject_offering.subject.name}",
            "paper": paper,
            "results": results,
            "avg_marks": round(float(stats["avg"] or 0), 2),
            "total": stats["total"],
            "pass_count": pass_count,
            "fail_count": stats["total"] - pass_count if paper.pass_marks else 0,
        })


# ══════════════════════════════════════════════════════════════
# STUDENT — MY RESULTS
# ══════════════════════════════════════════════════════════════

class StudentResultsView(StudentRequiredMixin, View):
    template_name = "web/exams/results/student.html"

    def get(self, request):
        college = _college(request)
        try:
            student = request.user.student_profile
        except Exception:
            return render(request, self.template_name, {
                "page_title": "My Results", "results": [],
            })
        results = (
            ExamResult.objects.filter(
                student=student, college=college,
                status=ExamResultStatus.PUBLISHED,
            )
            .select_related(
                "exam_paper__exam__section__batch__program",
                "exam_paper__exam__academic_year",
                "exam_paper__subject_offering__subject",
            )
            .order_by("-exam_paper__exam__created_at")
        )
        return render(request, self.template_name, {
            "page_title": "My Results",
            "results": results,
        })
