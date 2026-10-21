from rest_framework import serializers

from .models import Conversation, ConversationMessage,LongTermMemory


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class ConversationMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationMessage
        fields = [
            "id",
            "role",
            "content",
            "created_at",
        ]
        read_only_fields = fields


class LongTermMemoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LongTermMemory
        fields = ["id", "memory_type", "content", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_memory_type(self, value):
        if value != "PREFERENCE":
            raise serializers.ValidationError(
                "Only explicit user preferences can be saved through this endpoint."
            )
        return value

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Memory content cannot be empty."
            )
        return value.strip()        