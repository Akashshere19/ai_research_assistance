
import logging
from celery import shared_task
from django.db import transaction
from .models import Document
from .services import extract_document_content
from apps.documents.chunk_service import create_document_chunks
from apps.documents.vector_service import embed_document_chunks
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def ingest_document(self, document_id):
    try:
        with transaction.atomic():
            document = (
                Document.objects
                .select_for_update()
                .get(id=document_id)
            )

            if document.status  == "READY":
                return {
                    "document_id": str(document.id),
                    "status": document.status,
                }

            document.status = "PROCESSING"
            document.error_message = ""
            document.save(
                update_fields=[
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            file_path = document.file.path
            file_type = document.file_type

        extracted_text = extract_document_content(
            file_path,
            file_type,
        )

        if not extracted_text.strip():
            raise ValueError(
                "No readable text was extracted from the document."
            )

        with transaction.atomic():
            document = Document.objects.select_for_update().get(
                id=document_id
            )

            # Do not overwrite a document that another worker completed.
            if document.status == "READY":
                return {
                    "document_id": str(document.id),
                    "status": document.status,
                }

            document.extracted_text = extracted_text
            document.status = "PROCESSING"
            document.error_message = ""
            document.save(
                update_fields=[
                    "extracted_text",
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )
            create_document_chunks(document_id)
            embed_document_chunks(document_id)
            Document.objects.filter(
                id=document_id,
                status="PROCESSING",
            ).update(
                status="READY",
                error_message="",
            )
        return {
            "document_id": str(document_id),
            "status": "READY",
        }

    except Exception as exc:
        logger.exception(
            "Document ingestion failed for %s",
            document_id,
        )

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

        Document.objects.filter(id=document_id).update(
            status="FAILED",
            error_message="Document processing failed. Check server logs.",
        )
        raise
