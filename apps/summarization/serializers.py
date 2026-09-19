from rest_framework import serializers
from .models import Summary

class SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Summary
        fields = ['id', 'document', 'content', 'created_at']
        read_only_fields = ['content', 'created_at']