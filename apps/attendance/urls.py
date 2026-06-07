# apps/attendance/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.attendance.views import AttendanceRecordViewSet, AttendanceSessionViewSet

router = DefaultRouter()
router.register("sessions", AttendanceSessionViewSet, basename="attendance-session")
router.register("records", AttendanceRecordViewSet, basename="attendance-record")

urlpatterns = [path("", include(router.urls))]
