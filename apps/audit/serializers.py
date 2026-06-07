# apps/audit/serializers.py
from rest_framework import serializers
from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            "id", "college", "actor", "actor_email",
            "action", "entity_type", "entity_id",
            "payload", "ip_address", "user_agent", "created_at",
        ]
        read_only_fields = fields
