from django.urls import path
from .views import DocumentUploadView,RAGQueryView


urlpatterns = [
path(
        "projects/<uuid:project_id>/documents/",
        DocumentUploadView.as_view(),
        name="document-upload",
    ),
path("rag/query/", RAGQueryView.as_view(), name="rag-query"),
]