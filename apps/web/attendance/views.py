# apps/web/attendance/views.py
"""
Web views for the Attendance module.

Covered:
  AttendanceSessionListView  — teacher sees sessions for their offerings
  AttendanceSessionCreateView — open a new session
  AttendanceTakeView          — bulk mark all students in a session
  AttendanceSessionDetailView — see a single session's records
  StudentAttendanceSummaryView — student sees their own attendance across subjects
  AttendanceReportView        — admin sees summary by offering/student
"""
import logging
from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from apps.attendance.models import (
    AttendanceRecord, AttendanceSession,
    AttendanceSessionStatus, AttendanceStatus,
)
from apps.academics.models import Enrollment, SubjectOffering
from apps.web.attendance.forms import AttendanceSessionForm
from apps.web.mixins import (
    CollegeAdminRequiredMixin, StudentRequiredMixin, TeacherRequiredMixin,
)
from apps.platforms.permissions import ROLE_COLLEGE_ADMIN, _has_role

logger = logging.getLogger(__name__)


def _college(r):
    return r.college


# ══════════════════════════════════════════════════════════════
# SESSION LIST
# ══════════════════════════════════════════════════════════════

class AttendanceSessionListView(TeacherRequiredMixin, View):
    template_name = "web/attendance/session_list.html"

    def get(self, request):
        college = _college(request)
        qs = (
            AttendanceSession.objects.filter(college=college)
            .select_related(
                "subject_offering__subject",
                "subject_offering__section__batch__program",
                "subject_offering__term",
                "taken_by_teacher__user",
            )
            .order_by("-session_date", "-created_at")
        )
        # Teachers see only their own sessions
        if not _has_role(request.user, college, ROLE_COLLEGE_ADMIN) and not request.user.is_superuser:
            try:
                qs = qs.filter(taken_by_teacher=request.user.teacher_profile)
            except Exception:
                qs = qs.none()

        return render(request, self.template_name, {
            "page_title": "Attendance Sessions",
            "sessions": qs[:100],
        })


# ══════════════════════════════════════════════════════════════
# OPEN A NEW SESSION
# ══════════════════════════════════════════════════════════════

class AttendanceSessionCreateView(TeacherRequiredMixin, View):
    template_name = "web/attendance/session_form.html"

    def get(self, request):
        form = AttendanceSessionForm(college=_college(request))
        return render(request, self.template_name, {"page_title": "Open Session", "form": form})

    def post(self, request):
        college = _college(request)
        form = AttendanceSessionForm(request.POST, college=college)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Open Session", "form": form})
        cd = form.cleaned_data
        try:
            teacher = request.user.teacher_profile
        except Exception:
            teacher = None
        session = AttendanceSession.objects.create(
            college=college,
            subject_offering=cd["subject_offering"],
            session_date=cd["session_date"],
            start_time=cd.get("start_time"),
            end_time=cd.get("end_time"),
            taken_by_teacher=teacher,
            notes=cd.get("notes", ""),
            status=AttendanceSessionStatus.OPEN,
        )
        messages.success(request, "Session opened. Now mark attendance.")
        return redirect("web:attendance_take", session_id=session.id)


# ══════════════════════════════════════════════════════════════
# TAKE / BULK-MARK ATTENDANCE
# ══════════════════════════════════════════════════════════════

class AttendanceTakeView(TeacherRequiredMixin, View):
    template_name = "web/attendance/take.html"

    def get(self, request, session_id):
        college = _college(request)
        session = get_object_or_404(AttendanceSession, id=session_id, college=college)

        # All enrolled students in this section
        enrollments = (
            Enrollment.objects.filter(
                section=session.subject_offering.section,
                college=college,
                status="enrolled",
            )
            .select_related("student__user")
            .order_by("roll_no", "student__user__first_name")
        )

        # Existing records for this session (for pre-population)
        existing = {
            r.enrollment_id: r.attendance_status
            for r in AttendanceRecord.objects.filter(attendance_session=session)
        }

        students = []
        for enroll in enrollments:
            students.append({
                "enrollment": enroll,
                "current_status": existing.get(str(enroll.id), AttendanceStatus.PRESENT),
            })

        return render(request, self.template_name, {
            "page_title": f"Mark Attendance — {session.session_date}",
            "session": session,
            "students": students,
            "status_choices": AttendanceStatus.choices,
        })

    def post(self, request, session_id):
        college = _college(request)
        session = get_object_or_404(AttendanceSession, id=session_id, college=college)

        if session.status == AttendanceSessionStatus.CLOSED:
            messages.error(request, "This session is already closed.")
            return redirect("web:attendance_session_list")

        enrollments = Enrollment.objects.filter(
            section=session.subject_offering.section,
            college=college,
            status="enrolled",
        )

        valid_statuses = {s[0] for s in AttendanceStatus.choices}
        saved = 0
        for enroll in enrollments:
            key = f"status_{enroll.id}"
            raw_status = request.POST.get(key, AttendanceStatus.ABSENT)
            if raw_status not in valid_statuses:
                raw_status = AttendanceStatus.ABSENT

            AttendanceRecord.objects.update_or_create(
                attendance_session=session,
                enrollment=enroll,
                defaults={
                    "college": college,
                    "attendance_status": raw_status,
                    "marked_by": request.user,
                    "remarks": request.POST.get(f"remarks_{enroll.id}", ""),
                },
            )
            saved += 1

        # Close session if requested
        close_session = request.POST.get("close_session")
        if close_session:
            session.status = AttendanceSessionStatus.CLOSED
            session.save(update_fields=["status"])

        messages.success(request, f"Attendance saved for {saved} students.")
        return redirect("web:attendance_session_detail", session_id=session.id)


# ══════════════════════════════════════════════════════════════
# SESSION DETAIL
# ══════════════════════════════════════════════════════════════

class AttendanceSessionDetailView(TeacherRequiredMixin, View):
    template_name = "web/attendance/session_detail.html"

    def get(self, request, session_id):
        college = _college(request)
        session = get_object_or_404(AttendanceSession, id=session_id, college=college)
        records = (
            AttendanceRecord.objects.filter(attendance_session=session)
            .select_related("enrollment__student__user")
            .order_by("enrollment__roll_no", "enrollment__student__user__first_name")
        )
        # Stats
        total   = records.count()
        present = records.filter(attendance_status=AttendanceStatus.PRESENT).count()
        absent  = records.filter(attendance_status=AttendanceStatus.ABSENT).count()
        late    = records.filter(attendance_status=AttendanceStatus.LATE).count()

        return render(request, self.template_name, {
            "page_title": f"Session — {session.session_date}",
            "session": session,
            "records": records,
            "total": total, "present": present, "absent": absent, "late": late,
            "attendance_pct": round((present / total * 100) if total else 0, 1),
        })


# ══════════════════════════════════════════════════════════════
# STUDENT — MY ATTENDANCE
# ══════════════════════════════════════════════════════════════

class StudentAttendanceSummaryView(StudentRequiredMixin, View):
    template_name = "web/attendance/student_summary.html"

    def get(self, request):
        college = _college(request)
        try:
            student = request.user.student_profile
        except Exception:
            return render(request, self.template_name, {
                "page_title": "My Attendance", "summaries": [],
            })

        # Current enrollment
        enrollment = (
            Enrollment.objects.filter(student=student, college=college, status="enrolled")
            .select_related("section__batch__program")
            .first()
        )
        if not enrollment:
            return render(request, self.template_name, {
                "page_title": "My Attendance",
                "summaries": [],
                "enrollment": None,
            })

        # For each subject offering in the section: count sessions and present
        offerings = SubjectOffering.objects.filter(
            section=enrollment.section, college=college, status="active"
        ).select_related("subject", "term")

        summaries = []
        for offering in offerings:
            sessions = AttendanceSession.objects.filter(
                subject_offering=offering, college=college
            )
            total_sessions = sessions.count()
            present_count = AttendanceRecord.objects.filter(
                attendance_session__in=sessions,
                enrollment=enrollment,
                attendance_status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE],
            ).count()
            pct = round((present_count / total_sessions * 100) if total_sessions else 0, 1)
            summaries.append({
                "offering": offering,
                "total_sessions": total_sessions,
                "present_count": present_count,
                "absent_count": total_sessions - present_count,
                "percentage": pct,
                "low": pct < 75,
            })

        return render(request, self.template_name, {
            "page_title": "My Attendance",
            "enrollment": enrollment,
            "summaries": summaries,
        })


# ══════════════════════════════════════════════════════════════
# ADMIN — ATTENDANCE REPORT
# ══════════════════════════════════════════════════════════════

class AttendanceReportView(CollegeAdminRequiredMixin, View):
    template_name = "web/attendance/report.html"

    def get(self, request):
        college = _college(request)
        # Get all offerings with session counts
        offerings = (
            SubjectOffering.objects.filter(college=college, status="active")
            .select_related("subject", "section__batch__program", "term", "teacher__user")
            .annotate(session_count=Count("attendance_sessions"))
            .order_by("section__batch__name", "subject__name")
        )
        return render(request, self.template_name, {
            "page_title": "Attendance Report",
            "offerings": offerings,
        })
