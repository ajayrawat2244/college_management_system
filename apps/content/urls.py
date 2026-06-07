# apps/content/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.content.views import (
    AssignmentSubmissionViewSet,
    AssignmentViewSet,
    CourseMaterialViewSet,
    NoticeViewSet,
)

router = DefaultRouter()
router.register("materials", CourseMaterialViewSet, basename="course-material")
router.register("assignments", AssignmentViewSet, basename="assignment")
router.register("submissions", AssignmentSubmissionViewSet, basename="assignment-submission")
router.register("notices", NoticeViewSet, basename="notice")

urlpatterns = [path("", include(router.urls))]
