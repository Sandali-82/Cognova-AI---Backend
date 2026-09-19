from django.db import models
from apps.documents.models import Document

class Summary(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='summary')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Summary for {self.document.title}"
