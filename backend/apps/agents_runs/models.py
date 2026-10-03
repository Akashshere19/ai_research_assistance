from django.db import models
import uuid
# Create your models here.






class AgentRun(models.Model):
    STATUS = [("CREATED", "Created"),
    ("QUEUED", "Queued"),
    ("RUNNING", "Running"),
    ("COMPLETED", "Completed"),
    ("FAILED", "Failed"),]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4, 
        editable=False
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="agent_runs",
    )
    request = models.TextField()
    result = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20,choices=STATUS,default="QUEUED")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True,blank=True)
    completed_at = models.DateTimeField(null=True,blank=True)
    error_msg = models.TextField(null=True,blank=True)

    def __str__(self):
        return f"{self.id} - {self.request}"
