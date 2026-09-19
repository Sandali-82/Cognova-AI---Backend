from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'subject', 'file', 'extracted_text', 'uploaded_at']
        read_only_fields = ['extracted_text', 'uploaded_at']