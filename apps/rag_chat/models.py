from django.db import models
from django.contrib.auth.models import User
from apps.documents.models import Document
from pgvector.django import VectorField

class NoteChunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_text = models.TextField()
    chunk_index = models.IntegerField()
    embedding = VectorField(dimensions=768)  # Gemini embedding model output size
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['chunk_index']

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.title}"


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chat_messages')
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.question[:50]}"