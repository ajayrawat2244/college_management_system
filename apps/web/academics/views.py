# apps/web/academics/views.py
"""
Web views for the Academics module.

Covered:
  Departments  — list, create, edit
  Academic Years + Terms — list, create
  Programs     — list, create, edit
  Batches      — list (per program), create
  Sections     — list (per batch), create
  Subjects     — list, create, edit
  Subject Offerings — list, create
  Enrollments  — list (per section), add student
  Timetable    — list (per section/offering), create entry
"""
import logging
from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from apps.academics.models import (
    AcademicYear, Batch, Department, Enrollment,
    Program, Section, Subject, SubjectOffering,
    Term, TimetableEntry,
)
from apps.web.academics.forms import (
    AcademicYearForm, BatchForm, DepartmentForm, EnrollmentForm,
    ProgramForm, SectionForm, SubjectForm, SubjectOfferingForm,
    TermForm, TimetableEntryForm,
)
from apps.web.mixins import CollegeAdminRequiredMixin, StudentRequiredMixin, TeacherRequiredMixin

logger = logging.getLogger(__name__)


# ── helpers ──────────────────────────────────────────────────

def _college(request):
    return request.college


# ══════════════════════════════════════════════════════════════
# DEPARTMENTS
# ══════════════════════════════════════════════════════════════

class DepartmentListView(CollegeAdminRequiredMixin, View):
    template_name = "web/academics/departments/list.html"

    def get(self, request):
        depts = Department.objects.filter(college=_college(request)).order_by("name")
        return render(request, self.template_name, {
            "page_title": "Departments",
            "departments": depts,
            "form": DepartmentForm(),
        })

    def post(self, request):
        college = _college(request)
        form = DepartmentForm(request.POST)
        if not form.is_valid():
            depts = Department.objects.filter(college=college).order_by("name")
            return render(request, self.template_name, {
                "page_title": "Departments", "departments": depts, "form": form,
            })
        cd = form.cleaned_data
        try:
            Department.objects.create(
                college=college, code=cd["code"].upper(),
                name=cd["name"], description=cd.get("description", ""),
                status=cd["status"],
            )
            messages.success(request, f"Department '{cd['name']}' created.")
        except IntegrityError:
            form.add_error("code", "A department with this code already exists.")
            depts = Department.objects.filter(college=college).order_by("name")
            return render(request, self.template_name, {
                "page_title": "Departments", "departments": depts, "form": form,
            })
        return redirect("web:department_list")


class DepartmentEditView(CollegeAdminRequiredMixin, View):
    template_name = "web/academics/departments/edit.html"

    def get(self, request, dept_id):
        dept = get_object_or_404(Department, id=dept_id, college=_college(request))
        form = DepartmentForm(initial={
            "code": dept.code, "name": dept.name,
            "description": dept.description, "status": dept.status,
        })
        return render(request, self.template_name, {"page_title": "Edit Department", "dept": dept, "form": form})

    def post(self, request, dept_id):
        dept = get_object_or_404(Department, id=dept_id, college=_college(request))
        form = DepartmentForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Edit Department", "dept": dept, "form": form})
        cd = form.cleaned_data
        dept.code = cd["code"].upper(); dept.name = cd["name"]
        dept.description = cd.get("description", ""); dept.status = cd["status"]
        dept.save()
        messages.success(request, "Department updated.")
        return redirect("web:department_list")


# ══════════════════════════════════════════════════════════════
# ACADEMIC YEARS + TERMS
# ══════════════════════════════════════════════════════════════

class AcademicYearListView(CollegeAdminRequiredMixin, View):
    template_name = "web/academics/academic_years/list.html"

    def get(self, request):
        college = _college(request)
        years = AcademicYear.objects.filter(college=college).prefetch_related("terms").order_by("-start_date")
        return render(request, self.template_name, {
            "page_title": "Academic Years", "years": years, "form": AcademicYearForm(),
        })

    def post(self, request):
        college = _college(request)
        form = AcademicYearForm(request.POST)
        if not form.is_valid():
            years = AcademicYear.objects.filter(college=college).prefetch_related("terms").order_by("-start_date")
            return render(request, self.template_name, {"page_title": "Academic Years", "years": years, "form": form})
        cd = form.cleaned_data
        if cd.get("is_current"):
            AcademicYear.objects.filter(college=college, is_current=True).update(is_current=False)
        AcademicYear.objects.create(
            college=college, name=cd["name"], start_date=cd["start_date"],
            end_date=cd["end_date"], is_current=cd.get("is_current", False),
            status=cd["status"],
        )
        messages.success(request, f"Academic year '{cd['name']}' created.")
        return redirect("web:academic_year_list")


class TermCreateView(CollegeAdminRequiredMixin, View):
    template_name = "web/academics/academic_years/term_form.html"

    def get(self, request):
        form = TermForm(college=_college(request))
        return render(request, self.template_name, {"page_title": "Add Term", "form": form})

    def post(self, request):
        college = _college(request)
        form = TermForm(request.POST, college=college)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Add Term", "form": form})
        cd = form.cleaned_data
        if cd.get("is_current"):
            Term.objects.filter(college=college, is_current=True).update(is_current=False)
        Term.objects.create(
            college=college, academic_year=cd["academic_year"],
            term_no=cd["term_no"], name=cd["name"],
            start_date=cd["start_date"], end_date=cd["end_date"],
            is_current=cd.get("is_current", False), status=cd["status"],
        )
        messages.success(request, f"Term '{cd['name']}' created.")
        return redirect("web:academic_year_list")


# ══════════════════════════════════════════════════════════════
# PROGRAMS
# ══════════════════════════════════════════════════════════════

class ProgramListView(TeacherRequiredMixin, View):
    template_name = "web/academics/programs/list.html"

    def get(self, request):
        college = _college(request)
        programs = (
            Program.objects.filter(college=college)
            .select_related("department")
            .order_by("name")
        )
        return render(request, self.template_name, {
            "page_title": "Programs", "programs": programs,
        })


class ProgramCreateView(CollegeAdminRequiredMixin, View):
    template_name = "web/academics/programs/form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "page_title": "Add Program", "form": ProgramForm(college=_college(request)),
        })

    def post(self, request):
        college = _college(request)
        form = ProgramForm(request.POST, college=college)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Add Program", "form": form})
        cd = form.cleaned_data
        try:
            Program.objects.create(
                college=college, code=cd["code"].upper(), name=cd["name"],
                level=cd["level"], department=cd.get("department"),
                duration_terms=cd.get("duration_terms"), status=cd["status"],
            )
            messages.success(request, f"Program '{cd['name']}' created.")
            return redirect("web:program_list")
        except IntegrityError:
            form.add_error("code", "A program with this code already exists.")
            return render(request, self.template_name, {"page_title": "Add Program", "form": form})


class ProgramDetailView(TeacherRequiredMixin, View):
    template_name = "web/academics/programs/detail.html"

    def get(self, request, program_id):
        college = _college(request)
        program = get_object_or_404(Program, id=program_id, college=college)
        batches = Batch.objects.filter(program=program, college=college).select_related("academic_year").order_by("-academic_year__start_date")
        return render(request, self.template_name, {
            "page_title": program.name, "program": program, "batches": batches,
        })


# ══════════════════════════════════════════════════════════════
# BATCHES
# ══════════════════════════════════════════════════════════════

class BatchListView(TeacherRequiredMixin, View):
    template_name = "web/academics/batches/list.html"

    def get(self, request):
        college = _college(request)
        batches = (
            Batch.objects.filter(college=college)
            .select_related("program", "academic_year")
            .order_by("-academic_year__start_date", "program__name", "name")
        )
        return render(request, self.template_name, {"page_title": "Batches", "batches": batches})


class BatchCreateView(CollegeAdminRequiredMixin, View):
    template_name = "web/academics/batches/form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "page_title": "Add Batch", "form": BatchForm(college=_college(request)),
        })

    def post(self, request):
        college = _college(request)
        form = BatchForm(request.POST, college=college)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Add Batch", "form": form})
        cd = form.cleaned_data
        try:
            Batch.objects.create(
                college=college, program=cd["program"], academic_year=cd["academic_year"],
                name=cd["name"], intake_year=cd.get("intake_year"), status=cd["status"],
            )
            messages.success(request, f"Batch '{cd['name']}' created.")
            return redirect("web:batch_list")
        except IntegrityError:
            form.add_error(None, "A batch with this name already exists for this program and year.")
            return render(request, self.template_name, {"page_title": "Add Batch", "form": form})


# ══════════════════════════════════════════════════════════════
# SECTIONS
# ══════════════════════════════════════════════════════════════

class SectionListView(TeacherRequiredMixin, View):
    template_name = "web/academics/sections/list.html"

    def get(self, request):
        college = _college(request)
        sections = (
            Section.objects.filter(college=college)
            .select_related("batch__program", "batch__academic_year")
            .order_by("batch__program__name", "batch__name", "name")
        )
        return render(request, self.template_name, {"page_title": "Sections", "sections": sections})


class SectionCreateView(CollegeAdminRequiredMixin, View):
    template_name = "web/academics/sections/form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "page_title": "Add Section", "form": SectionForm(college=_college(request)),
        })

    def post(self, request):
        college = _college(request)
        form = SectionForm(request.POST, college=college)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Add Section", "form": form})
        cd = form.cleaned_data
        try:
            Section.objects.create(
                college=college, batch=cd["batch"], name=cd["name"],
                capacity=cd.get("capacity"), room=cd.get("room", ""), status=cd["status"],
            )
            messages.success(request, f"Section '{cd['name']}' created.")
            return redirect("web:section_list")
        except IntegrityError:
            form.add_error("name", "A section with this name already exists in this batch.")
            return render(request, self.template_name, {"page_title": "Add Section", "form": form})


class SectionDetailView(TeacherRequiredMixin, View):
    template_name = "web/academics/sections/detail.html"

    def get(self, request, section_id):
        college = _college(request)
        section = get_object_or_404(Section, id=section_id, college=college)
        enrollments = (
            Enrollment.objects.filter(section=section, college=college)
            .select_related("student__user")
            .order_by("roll_no", "student__user__first_name")
        )
        offerings = (
            SubjectOffering.objects.filter(section=section, college=college, status="active")
            .select_related("subject", "teacher__user", "term")
        )
        return render(request, self.template_name, {
            "page_title": f"Section {section.name}",
            "section": section,
            "enrollments": enrollments,
            "offerings": offerings,
            "enroll_count": enrollments.count(),
        })


# ══════════════════════════════════════════════════════════════
# SUBJECTS
# ══════════════════════════════════════════════════════════════

class SubjectListView(TeacherRequiredMixin, View):
    template_name = "web/academics/subjects/list.html"

    def get(self, request):
        college = _college(request)
        subjects = (
            Subject.objects.filter(college=college)
            .select_related("department")
            .order_by("name")
        )
        return render(request, self.template_name, {"page_title": "Subjects", "subjects": subjects})


class SubjectCreateView(CollegeAdminRequiredMixin, View):
    template_name = "web/academics/subjects/form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "page_title": "Add Subject", "form": SubjectForm(college=_college(request)),
        })

    def post(self, request):
        college = _college(request)
        form = SubjectForm(request.POST, college=college)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Add Subject", "form": form})
        cd = form.cleaned_data
        try:
            Subject.objects.create(
                college=college, code=cd["code"].upper(), name=cd["name"],
                credits=cd["credits"], subject_type=cd["subject_type"],
                department=cd.get("department"), status=cd["status"],
            )
            messages.success(request, f"Subject '{cd['name']}' created.")
            return redirect("web:subject_list")
        except IntegrityError:
            form.add_error("code", "A subject with this code already exists.")
            return render(request, self.template_name, {"page_title": "Add Subject", "form": form})


class SubjectDetailView(TeacherRequiredMixin, View):
    template_name = "web/academics/subjects/detail.html"

    def get(self, request, subject_id):
        college = _college(request)
        subject = get_object_or_404(Subject, id=subject_id, college=college)
        offerings = (
            SubjectOffering.objects.filter(subject=subject, college=college)
            .select_related("section__batch__program", "term", "teacher__user")
            .order_by("-term__start_date")
        )
        return render(request, self.template_name, {
            "page_title": subject.name, "subject": subject, "offerings": offerings,
        })


# ══════════════════════════════════════════════════════════════
# SUBJECT OFFERINGS
# ══════════════════════════════════════════════════════════════

class SubjectOfferingListView(TeacherRequiredMixin, View):
    template_name = "web/academics/offerings/list.html"

    def get(self, request):
        college = _college(request)
        # Teachers only see their own offerings; admins see all
        from apps.platforms.permissions import ROLE_COLLEGE_ADMIN
        from apps.platforms.permissions import _has_role
        qs = (
            SubjectOffering.objects.filter(college=college)
            .select_related("subject", "section__batch__program", "term", "teacher__user")
            .order_by("-term__start_date", "section__batch__name", "subject__name")
        )
        if not _has_role(request.user, college, ROLE_COLLEGE_ADMIN) and not request.user.is_superuser:
            try:
                teacher = request.user.teacher_profile
                qs = qs.filter(teacher=teacher)
            except Exception:
                qs = qs.none()
        return render(request, self.template_name, {"page_title": "Subject Offerings", "offerings": qs})


class SubjectOfferingCreateView(CollegeAdminRequiredMixin, View):
    template_name = "web/academics/offerings/form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "page_title": "Add Subject Offering",
            "form": SubjectOfferingForm(college=_college(request)),
        })

    def post(self, request):
        college = _college(request)
        form = SubjectOfferingForm(request.POST, college=college)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Add Subject Offering", "form": form})
        cd = form.cleaned_data
        try:
            SubjectOffering.objects.create(
                college=college, academic_year=cd["academic_year"], term=cd["term"],
                section=cd["section"], subject=cd["subject"], teacher=cd.get("teacher"),
                lecture_hours_per_week=cd.get("lecture_hours_per_week") or 0,
                room=cd.get("room", ""), status=cd["status"],
            )
            messages.success(request, "Subject offering created.")
            return redirect("web:offering_list")
        except IntegrityError:
            form.add_error(None, "This subject is already offered in this section for this term.")
            return render(request, self.template_name, {"page_title": "Add Subject Offering", "form": form})


# ══════════════════════════════════════════════════════════════
# ENROLLMENTS
# ══════════════════════════════════════════════════════════════

class EnrollmentListView(CollegeAdminRequiredMixin, View):
    template_name = "web/academics/enrollments/list.html"

    def get(self, request):
        college = _college(request)
        enrollments = (
            Enrollment.objects.filter(college=college)
            .select_related("student__user", "section__batch__program", "academic_year")
            .order_by("-academic_year__start_date", "section__batch__name", "roll_no")
        )
        return render(request, self.template_name, {"page_title": "Enrollments", "enrollments": enrollments})


class EnrollmentCreateView(CollegeAdminRequiredMixin, View):
    template_name = "web/academics/enrollments/form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "page_title": "Enroll Student",
            "form": EnrollmentForm(college=_college(request)),
        })

    def post(self, request):
        college = _college(request)
        form = EnrollmentForm(request.POST, college=college)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Enroll Student", "form": form})
        cd = form.cleaned_data
        try:
            Enrollment.objects.create(
                college=college, student=cd["student"], academic_year=cd["academic_year"],
                section=cd["section"], roll_no=cd.get("roll_no", ""), status=cd["status"],
            )
            messages.success(request, f"Student '{cd['student']}' enrolled.")
            return redirect("web:enrollment_list")
        except IntegrityError:
            form.add_error(None, "This student is already enrolled in this academic year / roll number conflict.")
            return render(request, self.template_name, {"page_title": "Enroll Student", "form": form})


# ══════════════════════════════════════════════════════════════
# TIMETABLE
# ══════════════════════════════════════════════════════════════

class TimetableView(TeacherRequiredMixin, View):
    template_name = "web/academics/timetable/list.html"

    def get(self, request):
        college = _college(request)
        entries = (
            TimetableEntry.objects.filter(college=college, status="active")
            .select_related(
                "subject_offering__subject",
                "subject_offering__section__batch__program",
                "subject_offering__teacher__user",
                "subject_offering__term",
            )
            .order_by("day_of_week", "start_time")
        )
        # Group by day
        from collections import defaultdict
        by_day = defaultdict(list)
        for e in entries:
            by_day[e.day_of_week].append(e)
        day_names = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"}
        timetable = [(day_names[d], by_day[d]) for d in sorted(by_day.keys())]
        return render(request, self.template_name, {
            "page_title": "Timetable", "timetable": timetable,
        })


class TimetableCreateView(CollegeAdminRequiredMixin, View):
    template_name = "web/academics/timetable/form.html"

    def get(self, request):
        return render(request, self.template_name, {
            "page_title": "Add Timetable Entry",
            "form": TimetableEntryForm(college=_college(request)),
        })

    def post(self, request):
        college = _college(request)
        form = TimetableEntryForm(request.POST, college=college)
        if not form.is_valid():
            return render(request, self.template_name, {"page_title": "Add Timetable Entry", "form": form})
        cd = form.cleaned_data
        try:
            TimetableEntry.objects.create(
                college=college, subject_offering=cd["subject_offering"],
                day_of_week=cd["day_of_week"], start_time=cd["start_time"],
                end_time=cd["end_time"], room=cd.get("room", ""),
            )
            messages.success(request, "Timetable entry added.")
            return redirect("web:timetable")
        except IntegrityError:
            form.add_error(None, "A timetable entry already exists for this offering at this time.")
            return render(request, self.template_name, {"page_title": "Add Timetable Entry", "form": form})
