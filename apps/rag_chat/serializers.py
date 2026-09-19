from rest_framework import serializers
from .models import ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'document', 'question', 'answer', 'created_at']
        read_only_fields = ['answer', 'created_at']