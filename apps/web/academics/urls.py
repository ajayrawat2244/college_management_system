# apps/web/academics/urls.py
from django.urls import path
from apps.web.academics.views import (
    AcademicYearListView, BatchCreateView, BatchListView,
    DepartmentEditView, DepartmentListView,
    EnrollmentCreateView, EnrollmentListView,
    ProgramCreateView, ProgramDetailView, ProgramListView,
    SectionCreateView, SectionDetailView, SectionListView,
    SubjectCreateView, SubjectDetailView, SubjectListView,
    SubjectOfferingCreateView, SubjectOfferingListView,
    TermCreateView, TimetableCreateView, TimetableView,
)

urlpatterns = [
    # Departments
    path("departments/",                     DepartmentListView.as_view(),     name="department_list"),
    path("departments/<uuid:dept_id>/edit/", DepartmentEditView.as_view(),     name="department_edit"),

    # Academic Years + Terms
    path("years/",                           AcademicYearListView.as_view(),   name="academic_year_list"),
    path("years/terms/add/",                 TermCreateView.as_view(),         name="term_create"),

    # Programs
    path("programs/",                        ProgramListView.as_view(),        name="program_list"),
    path("programs/add/",                    ProgramCreateView.as_view(),      name="program_create"),
    path("programs/<uuid:program_id>/",      ProgramDetailView.as_view(),      name="program_detail"),

    # Batches
    path("batches/",                         BatchListView.as_view(),          name="batch_list"),
    path("batches/add/",                     BatchCreateView.as_view(),        name="batch_create"),

    # Sections
    path("sections/",                        SectionListView.as_view(),        name="section_list"),
    path("sections/add/",                    SectionCreateView.as_view(),      name="section_create"),
    path("sections/<uuid:section_id>/",      SectionDetailView.as_view(),      name="section_detail"),

    # Subjects
    path("subjects/",                        SubjectListView.as_view(),        name="subject_list"),
    path("subjects/add/",                    SubjectCreateView.as_view(),      name="subject_create"),
    path("subjects/<uuid:subject_id>/",      SubjectDetailView.as_view(),      name="subject_detail"),

    # Subject Offerings
    path("offerings/",                       SubjectOfferingListView.as_view(), name="offering_list"),
    path("offerings/add/",                   SubjectOfferingCreateView.as_view(), name="offering_create"),

    # Enrollments
    path("enrollments/",                     EnrollmentListView.as_view(),     name="enrollment_list"),
    path("enrollments/add/",                 EnrollmentCreateView.as_view(),   name="enrollment_create"),

    # Timetable
    path("timetable/",                       TimetableView.as_view(),          name="timetable"),
    path("timetable/add/",                   TimetableCreateView.as_view(),    name="timetable_create"),
]
