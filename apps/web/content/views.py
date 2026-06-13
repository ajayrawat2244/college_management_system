# apps/web/content/views.py
"""
Web views for the Content module.

Covered:
  Course Materials — list, create, detail (admin/teacher)
  Assignments      — list, create, detail, submissions, grade (teacher) + submit (student)
  Notices          — list, create, detail, publish/archive (admin/teacher)
"""
import logging
from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from apps.content.models import (
    Assignment, AssignmentStatus, AssignmentSubmission, SubmissionStatus,
    CourseMaterial, MaterialStatus,
    Notice, NoticeStatus,
)
from apps.platforms.models import FileAsset
from apps.web.content.forms import (
    AssignmentForm, AssignmentSubmissionForm, CourseMaterialForm,
    GradeSubmissionForm, NoticeForm,
)
from apps.web.mixins import (
    CollegeAdminRequiredMixin, StudentRequiredMixin, TeacherRequiredMixin,
)
from apps.platforms.permissions import ROLE_COLLEGE_ADMIN, ROLE_TEACHER, _has_role

logger = logging.getLogger(__name__)


def _college(r):
    return r.college


def _save_file(request, field_name, college):
    """Save an uploaded file as a FileAsset and return it, or None."""
    f = request.FILES.get(field_name)
    if not f:
        return None
    try:
        asset = FileAsset.objects.create(
            college=college,
            original_filename=f.name,
            file_size=f.size,
            content_type=f.content_type or "application/octet-stream",
            uploaded_by=request.user,
            file=f,
        )
        return asset
    except Exception as exc:
        logger.warning("File save failed: %s", exc)
        return None


# ══════════════════════════════════════════════════════════════
# COURSE MATERIALS
# ══════════════════════════════════════════════════════════════

class CourseMaterialListView(TeacherRequiredMixin, View):
    template_name = "web/content/materials/list.html"

    def get(self, request):
        college = _college(request)
        is_admin = _has_role(request.user, college, ROLE_COLLEGE_ADMIN) or request.user.is_superuser
        is_teacher = _has_role(request.user, college, ROLE_TEACHER)

        qs = (
            CourseMaterial.objects.filter(college=college)
            .select_related("subject_offering__subject", "subject_offering__section__batch__program",
                            "subject", "created_by")
            .order_by("-created_at")
        )
        if not is_admin:
            if is_teacher:
                try:
                    teacher = request.user.teacher_profile
                    qs = qs.filter(
                        Q(created_by=request.user) |
                        Q(subject_offering__teacher=teacher)
                    )
                except Exception:
                    qs = qs.none()

        return render(request, self.template_name, {
            "page_title": "Course Materials",
            "materials": qs[:200],
            "can_create": is_admin or is_teacher,
        })


class CourseMaterialCreateView(TeacherRequiredMixin, View):
    template_name = "web/content/materials/form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "page_title": "Add Material",
            "form": CourseMaterialForm(college=_college(request)),
        })

    def post(self, request):
        college = _college(request)
        form = CourseMaterialForm(request.POST, request.FILES, college=college)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Add Material", "form": form})
        cd = form.cleaned_data
        file_asset = _save_file(request, "file_upload", college)
        is_published = cd["status"] == MaterialStatus.PUBLISHED
        CourseMaterial.objects.create(
            college=college,
            subject_offering=cd.get("subject_offering"),
            title=cd["title"],
            material_type=cd["material_type"],
            description=cd.get("description", ""),
            file_asset=file_asset,
            external_url=cd.get("external_url", ""),
            visibility=cd["visibility"],
            is_published=is_published,
            published_at=timezone.now() if is_published else None,
            created_by=request.user,
            status=cd["status"],
        )
        messages.success(request, f"Material '{cd['title']}' saved.")
        return redirect("web:material_list")


class CourseMaterialDetailView(TeacherRequiredMixin, View):
    template_name = "web/content/materials/detail.html"

    def get(self, request, material_id):
        college = _college(request)
        material = get_object_or_404(CourseMaterial, id=material_id, college=college)
        return render(request, self.template_name, {
            "page_title": material.title, "material": material,
        })

    def post(self, request, material_id):
        """Toggle publish/archive."""
        college = _college(request)
        if not _has_role(request.user, college, ROLE_COLLEGE_ADMIN, ROLE_TEACHER):
            messages.error(request, "Permission denied.")
            return redirect("web:material_list")
        material = get_object_or_404(CourseMaterial, id=material_id, college=college)
        action = request.POST.get("action")
        if action == "publish":
            material.status = MaterialStatus.PUBLISHED
            material.is_published = True
            material.published_at = timezone.now()
        elif action == "archive":
            material.status = MaterialStatus.ARCHIVED
            material.is_published = False
        material.save()
        messages.success(request, f"Material {action}ed.")
        return redirect("web:material_detail", material_id=material.id)


# ══════════════════════════════════════════════════════════════
# STUDENT — COURSE MATERIALS (read-only, published only)
# ══════════════════════════════════════════════════════════════

class StudentMaterialListView(StudentRequiredMixin, View):
    template_name = "web/content/materials/student_list.html"

    def get(self, request):
        college = _college(request)
        try:
            student = request.user.student_profile
            from apps.academics.models import Enrollment
            enrollment = (
                Enrollment.objects.filter(student=student, college=college, status="enrolled")
                .select_related("section")
                .first()
            )
        except Exception:
            enrollment = None

        qs = CourseMaterial.objects.filter(
            college=college,
            status=MaterialStatus.PUBLISHED,
        ).select_related("subject_offering__subject", "subject").order_by("-published_at")

        if enrollment:
            qs = qs.filter(
                Q(subject_offering__section=enrollment.section) |
                Q(subject_offering__isnull=True)
            )

        return render(request, self.template_name, {
            "page_title": "Course Materials",
            "materials": qs,
        })


# ══════════════════════════════════════════════════════════════
# ASSIGNMENTS — TEACHER/ADMIN
# ══════════════════════════════════════════════════════════════

class AssignmentListView(TeacherRequiredMixin, View):
    template_name = "web/content/assignments/list.html"

    def get(self, request):
        college = _college(request)
        is_admin = _has_role(request.user, college, ROLE_COLLEGE_ADMIN) or request.user.is_superuser
        qs = (
            Assignment.objects.filter(college=college)
            .select_related("subject_offering__subject",
                            "subject_offering__section__batch__program",
                            "created_by_teacher__user")
            .annotate(submission_count=Count("submissions"))
            .order_by("-created_at")
        )
        if not is_admin:
            try:
                teacher = request.user.teacher_profile
                qs = qs.filter(created_by_teacher=teacher)
            except Exception:
                qs = qs.none()

        return render(request, self.template_name, {
            "page_title": "Assignments",
            "assignments": qs,
        })


class AssignmentCreateView(TeacherRequiredMixin, View):
    template_name = "web/content/assignments/form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "page_title": "Create Assignment",
            "form": AssignmentForm(college=_college(request)),
        })

    def post(self, request):
        college = _college(request)
        form = AssignmentForm(request.POST, request.FILES, college=college)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Create Assignment", "form": form})
        cd = form.cleaned_data
        file_asset = _save_file(request, "file_upload", college)
        try:
            teacher = request.user.teacher_profile
        except Exception:
            teacher = None
        Assignment.objects.create(
            college=college,
            subject_offering=cd["subject_offering"],
            title=cd["title"],
            description=cd.get("description", ""),
            due_at=cd.get("due_at"),
            max_marks=cd["max_marks"],
            attachment_file_asset=file_asset,
            created_by_teacher=teacher,
            status=cd["status"],
        )
        messages.success(request, f"Assignment '{cd['title']}' created.")
        return redirect("web:assignment_list")


class AssignmentDetailView(TeacherRequiredMixin, View):
    """Teacher sees all submissions."""
    template_name = "web/content/assignments/detail.html"

    def get(self, request, assignment_id):
        college = _college(request)
        assignment = get_object_or_404(Assignment, id=assignment_id, college=college)
        submissions = (
            assignment.submissions.select_related("student__user")
            .order_by("student__user__first_name")
        )
        return render(request, self.template_name, {
            "page_title": assignment.title,
            "assignment": assignment,
            "submissions": submissions,
            "submitted_count": submissions.count(),
        })

    def post(self, request, assignment_id):
        """Toggle publish/close."""
        college = _college(request)
        assignment = get_object_or_404(Assignment, id=assignment_id, college=college)
        action = request.POST.get("action")
        if action == "publish":
            assignment.status = AssignmentStatus.PUBLISHED
        elif action == "close":
            assignment.status = AssignmentStatus.CLOSED
        assignment.save(update_fields=["status"])
        messages.success(request, f"Assignment {action}d.")
        return redirect("web:assignment_detail", assignment_id=assignment.id)


class GradeSubmissionView(TeacherRequiredMixin, View):
    """Grade a single student submission."""
    template_name = "web/content/assignments/grade.html"

    def get(self, request, assignment_id, submission_id):
        college = _college(request)
        assignment = get_object_or_404(Assignment, id=assignment_id, college=college)
        submission = get_object_or_404(AssignmentSubmission, id=submission_id, assignment=assignment)
        form = GradeSubmissionForm(initial={"marks_obtained": submission.marks_obtained})
        return render(request, self.template_name, {
            "page_title": "Grade Submission",
            "assignment": assignment,
            "submission": submission,
            "form": form,
        })

    def post(self, request, assignment_id, submission_id):
        college = _college(request)
        assignment = get_object_or_404(Assignment, id=assignment_id, college=college)
        submission = get_object_or_404(AssignmentSubmission, id=submission_id, assignment=assignment)
        form = GradeSubmissionForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {
                "page_title": "Grade Submission",
                "assignment": assignment, "submission": submission, "form": form,
            })
        cd = form.cleaned_data
        submission.marks_obtained = cd["marks_obtained"]
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.status = SubmissionStatus.GRADED
        submission.save()
        messages.success(request, f"Marks saved for {submission.student}.")
        return redirect("web:assignment_detail", assignment_id=assignment.id)


# ══════════════════════════════════════════════════════════════
# ASSIGNMENTS — STUDENT
# ══════════════════════════════════════════════════════════════

class StudentAssignmentListView(StudentRequiredMixin, View):
    template_name = "web/content/assignments/student_list.html"

    def get(self, request):
        college = _college(request)
        try:
            student = request.user.student_profile
            from apps.academics.models import Enrollment
            enrollment = Enrollment.objects.filter(
                student=student, college=college, status="enrolled"
            ).select_related("section").first()
        except Exception:
            enrollment = None

        assignments = []
        my_submissions = {}
        if enrollment:
            assignments = (
                Assignment.objects.filter(
                    subject_offering__section=enrollment.section,
                    college=college,
                    status__in=[AssignmentStatus.PUBLISHED, AssignmentStatus.CLOSED],
                )
                .select_related("subject_offering__subject")
                .order_by("due_at")
            )
            my_submissions = {
                s.assignment_id: s
                for s in AssignmentSubmission.objects.filter(
                    student=student, assignment__in=assignments
                )
            }

        return render(request, self.template_name, {
            "page_title": "My Assignments",
            "assignments": assignments,
            "my_submissions": my_submissions,
        })


class StudentSubmitAssignmentView(StudentRequiredMixin, View):
    template_name = "web/content/assignments/submit.html"

    def get(self, request, assignment_id):
        college = _college(request)
        assignment = get_object_or_404(
            Assignment, id=assignment_id, college=college,
            status__in=[AssignmentStatus.PUBLISHED],
        )
        try:
            existing = AssignmentSubmission.objects.get(
                assignment=assignment, student=request.user.student_profile
            )
        except AssignmentSubmission.DoesNotExist:
            existing = None
        return render(request, self.template_name, {
            "page_title": f"Submit — {assignment.title}",
            "assignment": assignment,
            "existing": existing,
            "form": AssignmentSubmissionForm(),
        })

    def post(self, request, assignment_id):
        college = _college(request)
        assignment = get_object_or_404(
            Assignment, id=assignment_id, college=college,
            status__in=[AssignmentStatus.PUBLISHED],
        )
        form = AssignmentSubmissionForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {
                "page_title": f"Submit — {assignment.title}",
                "assignment": assignment, "form": form,
            })
        cd = form.cleaned_data
        file_asset = _save_file(request, "file_upload", college)
        try:
            student = request.user.student_profile
        except Exception:
            messages.error(request, "Student profile not found.")
            return redirect("web:student_assignment_list")

        is_late = assignment.due_at and timezone.now() > assignment.due_at
        sub_status = SubmissionStatus.LATE if is_late else SubmissionStatus.SUBMITTED

        AssignmentSubmission.objects.update_or_create(
            assignment=assignment, student=student,
            defaults={
                "college": college,
                "submitted_at": timezone.now(),
                "file_asset": file_asset,
                "submission_text": cd.get("submission_text", ""),
                "status": sub_status,
            },
        )
        msg = "Submission saved (marked late — past due date)." if is_late else "Assignment submitted successfully."
        messages.success(request, msg)
        return redirect("web:student_assignment_list")


# ══════════════════════════════════════════════════════════════
# NOTICES
# ══════════════════════════════════════════════════════════════

class NoticeListView(TeacherRequiredMixin, View):
    template_name = "web/content/notices/list.html"

    def get(self, request):
        college = _college(request)
        is_admin = _has_role(request.user, college, ROLE_COLLEGE_ADMIN) or request.user.is_superuser
        qs = (
            Notice.objects.filter(college=college)
            .select_related("published_by", "target_section__batch__program")
            .order_by("-priority", "-created_at")
        )
        return render(request, self.template_name, {
            "page_title": "Notices",
            "notices": qs,
            "can_create": is_admin,
        })


class NoticeCreateView(CollegeAdminRequiredMixin, View):
    template_name = "web/content/notices/form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "page_title": "Post Notice",
            "form": NoticeForm(college=_college(request)),
        })

    def post(self, request):
        college = _college(request)
        form = NoticeForm(request.POST, request.FILES, college=college)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Post Notice", "form": form})
        cd = form.cleaned_data
        file_asset = _save_file(request, "file_upload", college)
        Notice.objects.create(
            college=college,
            title=cd["title"],
            body=cd["body"],
            audience_scope=cd["audience_scope"],
            target_section=cd.get("target_section"),
            file_asset=file_asset,
            published_by=request.user if cd["status"] == NoticeStatus.PUBLISHED else None,
            publish_at=cd.get("publish_at"),
            expires_at=cd.get("expires_at"),
            priority=cd.get("priority", 0),
            status=cd["status"],
        )
        messages.success(request, f"Notice '{cd['title']}' saved.")
        return redirect("web:notice_list")


class NoticeDetailView(TeacherRequiredMixin, View):
    template_name = "web/content/notices/detail.html"

    def get(self, request, notice_id):
        college = _college(request)
        notice = get_object_or_404(Notice, id=notice_id, college=college)
        return render(request, self.template_name, {"page_title": notice.title, "notice": notice})

    def post(self, request, notice_id):
        """Publish or archive a notice."""
        college = _college(request)
        if not _has_role(request.user, college, ROLE_COLLEGE_ADMIN) and not request.user.is_superuser:
            messages.error(request, "Only admins can change notice status.")
            return redirect("web:notice_detail", notice_id=notice_id)
        notice = get_object_or_404(Notice, id=notice_id, college=college)
        action = request.POST.get("action")
        if action == "publish":
            notice.status = NoticeStatus.PUBLISHED
            notice.published_by = request.user
            notice.publish_at = timezone.now()
        elif action == "archive":
            notice.status = NoticeStatus.ARCHIVED
        notice.save()
        messages.success(request, f"Notice {action}d.")
        return redirect("web:notice_detail", notice_id=notice.id)


class StudentNoticeListView(StudentRequiredMixin, View):
    """Students see published notices relevant to them."""
    template_name = "web/content/notices/student_list.html"

    def get(self, request):
        college = _college(request)
        now = timezone.now()
        qs = (
            Notice.objects.filter(
                college=college,
                status=NoticeStatus.PUBLISHED,
            )
            .filter(Q(publish_at__isnull=True) | Q(publish_at__lte=now))
            .filter(Q(expires_at__isnull=True) | Q(expires_at__gte=now))
            .select_related("published_by", "target_section")
            .order_by("-priority", "-publish_at")
        )
        return render(request, self.template_name, {
            "page_title": "Notices",
            "notices": qs,
        })
