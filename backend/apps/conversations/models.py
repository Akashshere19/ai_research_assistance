import uuid

from django.conf import settings
from django.db import models


class Conversation(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
    )

    title = models.CharField(
        max_length=200,
        default="New Conversation",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.title} - {self.user_id}"


class ConversationMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
    )

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(
                fields=["conversation", "created_at"],
                name="conv_msg_created_idx",
            ),
        ]

    def __str__(self):
        return f"{self.role} - {self.conversation_id}"
    

class LongTermMemory(models.Model):

    MEMORY_TYPES = [
        ("PREFERENCE", "Preference"),
        ("RESEARCH_CONTEXT", "Research Context"),
        ("REPORT_REFERENCE", "Report Reference"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="long_term_memories",
    )

    memory_type = models.CharField(
        max_length=30,
        choices=MEMORY_TYPES,
    )

    content = models.TextField()

    embedding = models.JSONField(
        default=list,
        blank=True,
    )

    source_run = models.ForeignKey(
        "agents_runs.AgentRun",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="long_term_memories",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )
    normalized_content = models.CharField(
    max_length=2000,
    blank=True,
    default="",
)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "normalized_content"],
                condition=models.Q(memory_type="PREFERENCE"),
                name="unique_user_preference_normalized",
            ),
        ]

    def __str__(self):
        return f"{self.memory_type} - {self.user_id}"    