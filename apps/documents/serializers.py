from pypdf import PdfReader
from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'subject', 'file', 'extracted_text', 'uploaded_at']
        read_only_fields = ['extracted_text', 'uploaded_at']

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        return value

    def validate_file(self, value):
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are supported.")
        max_size_mb = 10
        if value.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError(f"File size must not exceed {max_size_mb}MB.")

        # Reject files that only have a .pdf name but are corrupted, fake or password-protected
        try:
            reader = PdfReader(value)
            len(reader.pages)  # forces parsing; raises for unreadable or encrypted files
        except Exception:
            raise serializers.ValidationError(
                "This file is not a readable PDF (it may be corrupted or password-protected)."
            )
        finally:
            value.seek(0)  # rewind so the full file is still saved

        return value