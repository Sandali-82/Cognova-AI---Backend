from django.contrib import admin
from .models import NoteChunk, ChatMessage

@admin.register(NoteChunk)
class NoteChunkAdmin(admin.ModelAdmin):
    list_display = ('document', 'chunk_index')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'document', 'created_at')
