"""Admin for ChatMessage."""
from django.contrib import admin

from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "patient_case", "sender", "timestamp")
    list_filter = ("sender",)
    search_fields = ("content",)
    readonly_fields = ("timestamp",)
