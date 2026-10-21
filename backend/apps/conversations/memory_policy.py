
from apps.conversations.memory_service import save_memory
from apps.conversations.models import LongTermMemory




def save_user_preference(user, preference, source_run=None):
    if user is None or not user.is_authenticated:
        raise ValueError("An authenticated user is required.")

    if not preference or not preference.strip():
        raise ValueError("Preference cannot be empty.")

    content = preference.strip()
    normalized_content = content.casefold()

    existing = LongTermMemory.objects.filter(
        user=user,
        memory_type="PREFERENCE",
        normalized_content=normalized_content,
    ).first()

    if existing:
        return existing

    return save_memory(
        user=user,
        content=content,
        memory_type="PREFERENCE",
        source_run=source_run,
        normalized_content=normalized_content,
    )


def update_user_preference(user, memory_id, new_preference):
    if user is None or not user.is_authenticated:
        raise ValueError("An authenticated user is required.")

    if not new_preference or not new_preference.strip():
        raise ValueError("Preference cannot be empty.")

    memory = LongTermMemory.objects.get(
        id=memory_id,
        user=user,
        memory_type="PREFERENCE",
    )

    content = new_preference.strip()

    # If the preference is unchanged, avoid regenerating its embedding.
    if memory.content.strip().casefold() == content.casefold():
        return memory

    from apps.documents.embedding_service import generate_embedding

    memory.content = content
    memory.embedding = generate_embedding(content)
    memory.normalized_content = content.casefold()
    memory.save(
    update_fields=[
        "content",
        "embedding",
        "normalized_content",
        "updated_at",
    ]
)

    return memory

