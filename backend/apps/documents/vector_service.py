
from django.db import transaction

from .models import DocumentChunk
from .embedding_service import generate_embedding


def embed_document_chunks(document_id):
    chunks = DocumentChunk.objects.filter(
        document_id=document_id
    ).order_by("chunk_index")

    updated_count = 0

    for chunk in chunks.iterator():
        if chunk.embedding is not None:
            continue

        vector = generate_embedding(chunk.content)

        chunk.embedding = vector
        chunk.save(update_fields=["embedding"])

        updated_count += 1

    return updated_count
