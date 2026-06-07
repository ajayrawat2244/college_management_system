# apps/exams/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.exams.views import ExamPaperViewSet, ExamResultViewSet, ExamViewSet, GradingScaleViewSet

router = DefaultRouter()
router.register("grading-scales", GradingScaleViewSet, basename="grading-scale")
router.register("exams", ExamViewSet, basename="exam")
router.register("papers", ExamPaperViewSet, basename="exam-paper")
router.register("results", ExamResultViewSet, basename="exam-result")

urlpatterns = [path("", include(router.urls))]
