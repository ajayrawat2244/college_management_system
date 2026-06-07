# apps/exams/serializers.py
from rest_framework import serializers

from apps.exams.models import Exam, ExamPaper, ExamResult, GradingScale


class GradingScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradingScale
        fields = [
            "id", "college", "grade_label", "min_percentage", "max_percentage",
            "grade_point", "remarks", "effective_from", "effective_to", "status",
        ]
        read_only_fields = ["id", "college"]


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = [
            "id", "college", "academic_year", "term", "section",
            "name", "exam_type", "start_date", "end_date", "status", "created_at",
        ]
        read_only_fields = ["id", "college", "created_at"]


class ExamPaperSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject_offering.subject.name", read_only=True)

    class Meta:
        model = ExamPaper
        fields = [
            "id", "college", "exam", "subject_offering", "subject_name",
            "exam_date", "start_time", "end_time",
            "max_marks", "pass_marks", "room", "status",
        ]
        read_only_fields = ["id", "college"]


class ExamResultSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    admission_no = serializers.CharField(source="student.admission_no", read_only=True)

    class Meta:
        model = ExamResult
        fields = [
            "id", "college", "exam_paper", "student", "student_name", "admission_no",
            "marks_obtained", "grade_label", "grade_point",
            "remarks", "evaluated_by", "evaluated_at", "status",
        ]
        read_only_fields = ["id", "college", "evaluated_by", "evaluated_at"]

    def get_student_name(self, obj):
        u = obj.student.user
        return f"{u.first_name} {u.last_name or ''}".strip()
