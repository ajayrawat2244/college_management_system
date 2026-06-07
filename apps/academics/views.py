# apps/academics/views.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.academics.models import (
    AcademicYear,
    Department,
    Enrollment,
    Program,
    Section,
    Subject,
    SubjectOffering,
    Term,
)
from apps.academics.serializers import (
    AcademicYearSerializer,
    DepartmentSerializer,
    EnrollmentSerializer,
    ProgramSerializer,
    SectionSerializer,
    SubjectOfferingSerializer,
    SubjectSerializer,
    TermSerializer,
)
from apps.platforms.mixins import CollegeScopedMixin
from apps.platforms.permissions import IsCollegeAdmin, IsCollegeAdminOrTeacher, IsTenantResolved


class AcademicYearViewSet(CollegeScopedMixin, ModelViewSet):
    queryset = AcademicYear.objects.all().order_by("-start_date")
    serializer_class = AcademicYearSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["is_current", "status"]


class TermViewSet(CollegeScopedMixin, ModelViewSet):
    queryset = Term.objects.select_related("academic_year").all().order_by("-start_date")
    serializer_class = TermSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["academic_year", "is_current", "status"]


class DepartmentViewSet(CollegeScopedMixin, ModelViewSet):
    queryset = Department.objects.all().order_by("name")
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdminOrTeacher]
    filterset_fields = ["status"]
    search_fields = ["name", "code"]


class ProgramViewSet(CollegeScopedMixin, ModelViewSet):
    queryset = Program.objects.select_related("department").all().order_by("name")
    serializer_class = ProgramSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["department", "status", "degree_type"]
    search_fields = ["name", "code"]


class SectionViewSet(CollegeScopedMixin, ModelViewSet):
    queryset = Section.objects.select_related("program", "academic_year").all()
    serializer_class = SectionSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdminOrTeacher]
    filterset_fields = ["program", "academic_year", "status", "year_of_study"]
    search_fields = ["name"]


class SubjectViewSet(CollegeScopedMixin, ModelViewSet):
    queryset = Subject.objects.select_related("department").all().order_by("name")
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdminOrTeacher]
    filterset_fields = ["department", "subject_type", "status"]
    search_fields = ["name", "code"]


class SubjectOfferingViewSet(CollegeScopedMixin, ModelViewSet):
    queryset = SubjectOffering.objects.select_related(
        "subject", "section", "teacher", "academic_year", "term"
    ).all()
    serializer_class = SubjectOfferingSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdminOrTeacher]
    filterset_fields = ["academic_year", "term", "section", "teacher", "status"]
    search_fields = ["subject__name", "section__name"]


class EnrollmentViewSet(CollegeScopedMixin, ModelViewSet):
    queryset = Enrollment.objects.select_related(
        "student__user", "section", "academic_year"
    ).all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsTenantResolved, IsCollegeAdmin]
    filterset_fields = ["section", "academic_year", "status"]
    search_fields = ["student__admission_no", "roll_no"]
