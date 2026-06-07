# apps/content/serializers.py
from rest_framework import serializers

from apps.content.models import Assignment, AssignmentSubmission, CourseMaterial, Notice


class CourseMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseMaterial
        fields = [
            "id", "college", "subject_offering", "subject",
            "title", "material_type", "description",
            "file_asset", "external_url", "visibility",
            "is_published", "published_at", "created_by", "status", "created_at",
        ]
        read_only_fields = ["id", "college", "created_by", "published_at", "created_at"]

    def validate(self, data):
        if not data.get("subject_offering") and not data.get("subject"):
            raise serializers.ValidationError(
                "Either subject_offering or subject must be provided."
            )
        return data


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = [
            "id", "college", "subject_offering", "title", "description",
            "due_at", "max_marks", "attachment_file_asset",
            "created_by_teacher", "status", "created_at",
        ]
        read_only_fields = ["id", "college", "created_by_teacher", "created_at"]


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = AssignmentSubmission
        fields = [
            "id", "college", "assignment", "student", "student_name",
            "submitted_at", "file_asset", "submission_text",
            "marks_obtained", "graded_by", "graded_at", "status",
        ]
        read_only_fields = ["id", "college", "graded_by", "graded_at"]

    def get_student_name(self, obj):
        u = obj.student.user
        return f"{u.first_name} {u.last_name or ''}".strip()


class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = [
            "id", "college", "title", "body", "audience_scope",
            "target_section", "target_role", "file_asset",
            "published_by", "publish_at", "expires_at",
            "priority", "status", "created_at",
        ]
        read_only_fields = ["id", "college", "published_by", "created_at"]
