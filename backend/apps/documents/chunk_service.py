
from django.db import transaction

from .models import Document, DocumentChunk
from .chunking import split_text


def create_document_chunks(document_id):
    document = Document.objects.get(id=document_id)

    if document.status != "PROCESSING":
        raise ValueError("Document must be PROCESSING before chunking.")

    if not document.extracted_text.strip():
        raise ValueError("Document has no extracted text.")

    chunks = split_text(
        document.extracted_text,
        chunk_size=1000,
        chunk_overlap=150,
    )

    with transaction.atomic():
        # Remove old chunks when reprocessing a document.
        DocumentChunk.objects.filter(document=document).delete()

        DocumentChunk.objects.bulk_create([
            DocumentChunk(
                document=document,
                chunk_index=index,
                content=content,
            )
            for index, content in enumerate(chunks)
        ])

    return len(chunks)
