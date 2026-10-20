
import numpy as np

from .models import DocumentChunk
from .embedding_service import generate_embedding


def retrieve_relevant_chunks(
     question: str,
    document_id=None,
    allowed_document_ids=None,
    top_k: int = 5,
    min_similarity: float = 0.35,
) -> list[dict]:
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    queryset = DocumentChunk.objects.filter(
    embedding__isnull=False,
    document_id__in=allowed_document_ids or [],
    document__status="READY",
)

    if document_id is not None:
            queryset = queryset.filter(document_id=document_id)

    query_vector = np.asarray(
        generate_embedding(question),
        dtype=np.float32,
    )

    results = []

    for chunk in queryset:
        vector = np.asarray(chunk.embedding, dtype=np.float32)

        if vector.shape != query_vector.shape:
            continue

        # Embeddings are normalized, so dot product equals cosine similarity.
        similarity = float(np.dot(query_vector, vector))

        if similarity >= min_similarity:
            results.append({
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "filename": chunk.document.original_filename,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "similarity": similarity,
            })

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True,
    )

    return results[:top_k]
