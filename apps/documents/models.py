from django.db import models
from django.contrib.auth.models import User

class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=100, blank=True, null=True)  # e.g. "Biology", "Chemistry"
    file = models.FileField(upload_to='documents/')
    extracted_text = models.TextField(blank=True, null=True)  # PDF text extraction result
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title