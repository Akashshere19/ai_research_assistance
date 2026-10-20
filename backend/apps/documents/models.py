import uuid
from django.db import models
from django.conf import settings

# Create your models here.




class Document(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("READY", "Ready"),
        ("FAILED", "Failed"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="documents",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_documents",
    )

    file = models.FileField(upload_to="rag_documents/%Y/%m/")

    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    extracted_text = models.TextField(blank=True, default="")
    error_message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.original_filename



class DocumentChunk(models.Model):
      id  = models.UUIDField(
           primary_key = True,
           default = uuid.uuid4,
           editable=False 
      )
      document = models.ForeignKey(Document,on_delete=models.CASCADE,
                                   related_name="chunks")
      
      chunk_index = models.PositiveIntegerField()
      content = models.TextField()
      created_at = models.DateTimeField(auto_now_add=True)
      embedding = models.JSONField(
    null=True,
    blank=True,
)

      class Meta:
           ordering = ['chunk_index']
           constraints = [
                models.UniqueConstraint(
                     fields= ['document','chunk_index'],
                     name = 'unique_document_chunk_index',
                )
           ]

           def __str__(self):
                return f"{self.document.original_filename} - Chunk {self.chunk_index}"
