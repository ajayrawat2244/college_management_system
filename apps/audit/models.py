#audit/models.py
import uuid

from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    college = models.ForeignKey(
        "platforms.College",
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="audit_actions",
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=120)
    entity_type = models.CharField(max_length=120)
    entity_id = models.UUIDField(null=True, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "audit_logs"
        indexes = [
            models.Index(fields=["college", "created_at"], name="idx_audit_col_dt"),
            models.Index(fields=["entity_type", "entity_id"], name="idx_audit_logs_entity"),
        ]

    def __str__(self):
        return f"{self.action} - {self.entity_type}"