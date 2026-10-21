from django.urls import path

from .views import (
    ConversationListCreateView,
    ConversationDetailView,
    LongTermMemoryListCreateView,
    LongTermMemoryDetailView
)

urlpatterns = [
    path(
        "",
        ConversationListCreateView.as_view(),
        name="conversation-list-create",
    ),
    path(
        "<uuid:conversation_id>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    path(
    "memories/",
    LongTermMemoryListCreateView.as_view(),
    name="memory-list-create",
),

path(
    "memories/<uuid:memory_id>/",
    LongTermMemoryDetailView.as_view(),
    name="memory-detail",
),

]