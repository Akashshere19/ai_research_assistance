
from pathlib import Path
from .models import Document
from rest_framework import serializers


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
    ".md",
    ".csv",
    ".xlsx",
    ".docx"
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "project",
            "file",
            "original_filename",
            "file_type",
            "status",
            "error_message",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "original_filename",
            "file_type",
            "status",
            "error_message",
            "created_at",
        ]

    def validate_file(self, uploaded_file):
        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                "Unsupported file type. Upload PDF, image, TXT, "
                "Markdown, CSV, or XLSX files."
            )

        if uploaded_file.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                "File size must not exceed 20 MB."
            )

        return uploaded_file

    def create(self, validated_data):
        uploaded_file = validated_data["file"]

        validated_data["original_filename"] = Path(
            uploaded_file.name
        ).name
        validated_data["file_type"] = (
            Path(uploaded_file.name).suffix.lower().lstrip(".")
        )

        return super().create(validated_data)


class RAGQuerySerializer(serializers.Serializer):
    question = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=2000,
    )
    document_id = serializers.UUIDField(
        required=False,
        allow_null=True,
    )
    top_k = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=10,
    )
    