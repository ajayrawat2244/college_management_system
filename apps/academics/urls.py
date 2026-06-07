# apps/academics/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.academics.views import (
    AcademicYearViewSet,
    DepartmentViewSet,
    EnrollmentViewSet,
    ProgramViewSet,
    SectionViewSet,
    SubjectOfferingViewSet,
    SubjectViewSet,
    TermViewSet,
)

router = DefaultRouter()
router.register("academic-years", AcademicYearViewSet, basename="academic-year")
router.register("terms", TermViewSet, basename="term")
router.register("departments", DepartmentViewSet, basename="department")
router.register("programs", ProgramViewSet, basename="program")
router.register("sections", SectionViewSet, basename="section")
router.register("subjects", SubjectViewSet, basename="subject")
router.register("subject-offerings", SubjectOfferingViewSet, basename="subject-offering")
router.register("enrollments", EnrollmentViewSet, basename="enrollment")

urlpatterns = [path("", include(router.urls))]
