# apps/web/attendance/urls.py
from django.urls import path
from apps.web.attendance.views import (
    AttendanceReportView,
    AttendanceSessionCreateView,
    AttendanceSessionDetailView,
    AttendanceSessionListView,
    AttendanceTakeView,
    StudentAttendanceSummaryView,
)

urlpatterns = [
    path("",                             AttendanceSessionListView.as_view(),   name="attendance_session_list"),
    path("open/",                        AttendanceSessionCreateView.as_view(), name="attendance_session_create"),
    path("<uuid:session_id>/",           AttendanceSessionDetailView.as_view(), name="attendance_session_detail"),
    path("<uuid:session_id>/mark/",      AttendanceTakeView.as_view(),          name="attendance_take"),
    path("my/",                          StudentAttendanceSummaryView.as_view(), name="my_attendance"),
    path("report/",                      AttendanceReportView.as_view(),        name="attendance_report"),
]
