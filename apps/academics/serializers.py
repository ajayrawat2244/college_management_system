# apps/academics/serializers.py
from rest_framework import serializers

from apps.academics.models import (
    AcademicYear,
    Department,
    Enrollment,
    Program,
    Section,
    Subject,
    SubjectOffering,
    Term,
)


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = ["id", "college", "name", "start_date", "end_date", "is_current", "status", "created_at"]
        read_only_fields = ["id", "college", "created_at"]


class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = ["id", "college", "academic_year", "name", "start_date", "end_date", "is_current", "status"]
        read_only_fields = ["id", "college"]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "college", "code", "name", "description", "status", "created_at"]
        read_only_fields = ["id", "college", "created_at"]


class ProgramSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Program
        fields = [
            "id", "college", "code", "name", "department", "department_name",
            "duration_years", "degree_type", "status", "created_at",
        ]
        read_only_fields = ["id", "college", "created_at"]


class SectionSerializer(serializers.ModelSerializer):
    program_name = serializers.CharField(source="program.name", read_only=True)
    academic_year_name = serializers.CharField(source="academic_year.name", read_only=True)

    class Meta:
        model = Section
        fields = [
            "id", "college", "program", "program_name",
            "academic_year", "academic_year_name",
            "name", "year_of_study", "max_students", "status", "created_at",
        ]
        read_only_fields = ["id", "college", "created_at"]


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = [
            "id", "college", "code", "name", "department",
            "credits", "subject_type", "status", "created_at",
        ]
        read_only_fields = ["id", "college", "created_at"]


class SubjectOfferingSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    section_name = serializers.CharField(source="section.name", read_only=True)

    class Meta:
        model = SubjectOffering
        fields = [
            "id", "college", "academic_year", "term", "subject", "subject_name",
            "section", "section_name", "teacher", "status", "created_at",
        ]
        read_only_fields = ["id", "college", "created_at"]


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    section_name = serializers.CharField(source="section.name", read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            "id", "college", "student", "student_name",
            "section", "section_name", "academic_year",
            "roll_no", "status", "enrolled_at",
        ]
        read_only_fields = ["id", "college", "enrolled_at"]

    def get_student_name(self, obj):
        u = obj.student.user
        return f"{u.first_name} {u.last_name or ''}".strip()
