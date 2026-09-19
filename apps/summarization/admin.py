from django.contrib import admin
from .models import Summary

@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ('document', 'created_at')
