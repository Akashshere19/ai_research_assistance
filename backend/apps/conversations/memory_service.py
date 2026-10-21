
import math

from apps.conversations.models import LongTermMemory
from apps.documents.embedding_service import generate_embedding



def save_memory(
    user,
    content,
    memory_type,
    source_run=None,
    normalized_content=None,
):
    content = content.strip()

    if not content:
        raise ValueError("Memory content cannot be empty.")

    embedding = generate_embedding(content)

    if normalized_content is None:
        normalized_content = content.strip().casefold()

    return LongTermMemory.objects.create(
        user=user,
        content=content,
        normalized_content=normalized_content,
        memory_type=memory_type,
        embedding=embedding,
        source_run=source_run,
    )



def cosine_similarity(vector_a, vector_b):
    if not vector_a or not vector_b:
        return 0.0

    if len(vector_a) != len(vector_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def search_memories(user, query, limit=5, min_similarity=0.5):
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if limit < 1:
        raise ValueError("Limit must be at least 1.")

    query_embedding = generate_embedding(query)

    # Filter by user before calculating similarity.
    memories = LongTermMemory.objects.filter(
        user=user,
    ).exclude(embedding=[])

    ranked_memories = []

    for memory in memories.iterator():
        similarity = cosine_similarity(
            query_embedding,
            memory.embedding,
        )

        if similarity >= min_similarity:
            ranked_memories.append((similarity, memory))

    ranked_memories.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        {
            "memory": memory,
            "similarity": similarity,
        }
        for similarity, memory in ranked_memories[:limit]
    ]
