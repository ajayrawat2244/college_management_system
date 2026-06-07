from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.accounts.models import StudentProfile
from apps.academics.models import Enrollment, SubjectOffering, TimetableEntry
from apps.content.models import CourseMaterial
from apps.finance.models import FeeInvoice, FeePayment, FeePaymentStatus


def _money(value):
    return value if value is not None else Decimal("0.00")


def get_dashboard_context(college):
    today = timezone.localdate()

    total_students = StudentProfile.objects.filter(college=college).count()
    total_admissions = Enrollment.objects.filter(college=college).count()
    total_revenue = _money(
        FeePayment.objects.filter(
            college=college,
            status=FeePaymentStatus.SUCCESSFUL,
        ).aggregate(total=Sum("amount"))["total"]
    )
    active_courses = SubjectOffering.objects.filter(college=college, status="active").count()
    pending_fee_qs = FeeInvoice.objects.filter(college=college, balance_amount__gt=0)
    pending_fee_count = pending_fee_qs.count()
    pending_fee_amount = _money(
        pending_fee_qs.aggregate(total=Sum("balance_amount"))["total"]
    )
    published_contents = CourseMaterial.objects.filter(
        college=college,
        is_published=True,
    ).count()
    upcoming_live_classes = TimetableEntry.objects.filter(
        college=college,
        day_of_week=today.isoweekday(),
        status="active",
    ).count()

    recent_students = list(
        StudentProfile.objects.filter(college=college)
        .select_related("user")
        .prefetch_related(
            "enrollments__section__batch__program",
            "enrollments__academic_year",
        )
        .order_by("-created_at")[:5]
    )

    for student in recent_students:
        enrollments = list(student.enrollments.all())
        student.latest_enrollment = enrollments[0] if enrollments else None
        student.display_name = f"{student.user.first_name} {student.user.last_name or ''}".strip()

    return {
        "total_students": total_students,
        "total_admissions": total_admissions,
        "total_revenue": total_revenue,
        "active_courses": active_courses,
        "pending_fee_count": pending_fee_count,
        "pending_fee_amount": pending_fee_amount,
        "published_contents": published_contents,
        "upcoming_live_classes": upcoming_live_classes,
        "recent_students": recent_students,
    }
