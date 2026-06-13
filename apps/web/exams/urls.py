# apps/web/exams/urls.py
from django.urls import path
from apps.web.exams.views import (
    ExamCreateView, ExamDetailView, ExamListView,
    ExamPaperCreateView,
    ExamResultDetailView, ExamResultEntryView,
    GradingScaleListView, StudentResultsView,
)

urlpatterns = [
    path("grading/",                          GradingScaleListView.as_view(),  name="grading_scale_list"),
    path("",                                  ExamListView.as_view(),          name="exam_list"),
    path("create/",                           ExamCreateView.as_view(),        name="exam_create"),
    path("<uuid:exam_id>/",                   ExamDetailView.as_view(),        name="exam_detail"),
    path("<uuid:exam_id>/papers/add/",        ExamPaperCreateView.as_view(),   name="exam_paper_create"),
    path("papers/<uuid:paper_id>/results/",   ExamResultEntryView.as_view(),   name="exam_result_entry"),
    path("papers/<uuid:paper_id>/results/view/", ExamResultDetailView.as_view(), name="exam_result_detail"),
    path("my-results/",                       StudentResultsView.as_view(),    name="student_results"),
]
