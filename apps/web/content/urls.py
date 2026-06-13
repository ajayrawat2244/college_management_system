# apps/web/content/urls.py
from django.urls import path
from apps.web.content.views import (
    AssignmentCreateView, AssignmentDetailView, AssignmentListView,
    CourseMaterialCreateView, CourseMaterialDetailView, CourseMaterialListView,
    GradeSubmissionView,
    NoticeCreateView, NoticeDetailView, NoticeListView,
    StudentAssignmentListView, StudentMaterialListView,
    StudentNoticeListView, StudentSubmitAssignmentView,
)

urlpatterns = [
    # Materials
    path("materials/",                              CourseMaterialListView.as_view(),     name="material_list"),
    path("materials/add/",                          CourseMaterialCreateView.as_view(),   name="material_create"),
    path("materials/<uuid:material_id>/",           CourseMaterialDetailView.as_view(),   name="material_detail"),
    path("materials/student/",                      StudentMaterialListView.as_view(),    name="student_material_list"),

    # Assignments — teacher/admin
    path("assignments/",                            AssignmentListView.as_view(),         name="assignment_list"),
    path("assignments/add/",                        AssignmentCreateView.as_view(),       name="assignment_create"),
    path("assignments/<uuid:assignment_id>/",       AssignmentDetailView.as_view(),       name="assignment_detail"),
    path("assignments/<uuid:assignment_id>/submissions/<uuid:submission_id>/grade/",
         GradeSubmissionView.as_view(), name="grade_submission"),

    # Assignments — student
    path("assignments/mine/",                       StudentAssignmentListView.as_view(),  name="student_assignment_list"),
    path("assignments/<uuid:assignment_id>/submit/", StudentSubmitAssignmentView.as_view(), name="submit_assignment"),

    # Notices
    path("notices/",                                NoticeListView.as_view(),             name="notice_list"),
    path("notices/add/",                            NoticeCreateView.as_view(),           name="notice_create"),
    path("notices/<uuid:notice_id>/",               NoticeDetailView.as_view(),           name="notice_detail"),
    path("notices/board/",                          StudentNoticeListView.as_view(),      name="notice_board"),
]
