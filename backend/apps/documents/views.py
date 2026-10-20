
from .models import Document
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import APIView
from .serializers import DocumentUploadSerializer,RAGQuerySerializer
from rest_framework.parsers import FormParser, MultiPartParser
from .tasks import ingest_document
from django.db import transaction

from .answer_service import answer_question






class DocumentUploadView(generics.CreateAPIView):
    serializer_class = DocumentUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return Document.objects.filter(
            uploaded_by=self.request.user
        )

    def perform_create(self, serializer):
            project = serializer.validated_data["project"]

            if str(project.id) != str(self.kwargs["project_id"]):
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    "project": "Project ID does not match URL."
                })

            if project.owner_id != self.request.user.id:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(
                    "You do not have access to this project."
                )

            document = serializer.save(uploaded_by=self.request.user)

            transaction.on_commit(
                lambda: ingest_document.delay(str(document.id))
            )


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["project_id"] = self.kwargs["project_id"]
        return context
    

class RAGQueryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RAGQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        document_id = data.get("document_id")

        documents = Document.objects.filter(
            uploaded_by=request.user,
            status="READY",
        )
        allowed_document_ids = documents.values_list("id", flat=True)

        if document_id:
            documents = documents.filter(id=document_id)

            if not documents.exists():
                return Response(
                    {"detail": "Document not found or not accessible."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        result = answer_question(
                question=serializer.validated_data["question"],
                document_id=document_id,
                allowed_document_ids=allowed_document_ids,
                top_k=serializer.validated_data["top_k"],
        )

        return Response(result, status=status.HTTP_200_OK)    