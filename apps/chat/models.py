"""Per-case chat history for the RAG chatbot."""
from django.db import models


class ChatMessage(models.Model):
    """One message in a case-scoped conversation. sender is an enum because BOT is not a user."""

    SENDER_CLINICIAN = "CLINICIAN"
    SENDER_BOT = "BOT"
    SENDER_CHOICES = [
        (SENDER_CLINICIAN, "Clinician"),
        (SENDER_BOT, "Bot"),
    ]

    patient_case = models.ForeignKey(
        "cases.PatientCase",
        on_delete=models.CASCADE,
        related_name="chat_messages",
    )
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "chat_messages"
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["patient_case", "timestamp"]),
        ]

    def __str__(self) -> str:
        return f"{self.sender} @ case #{self.patient_case_id} ({self.timestamp:%Y-%m-%d %H:%M})"

    @property
    def is_bot(self) -> bool:
        return self.sender == self.SENDER_BOT
