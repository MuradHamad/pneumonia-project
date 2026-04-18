"""Chat views — POST a query, save user + bot messages."""
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import clinician_required
from apps.cases.models import PatientCase
from services import chatbot

from .models import ChatMessage


@clinician_required
@require_POST
def send_message(request, case_id: int):
    """Append clinician query + bot reply to a case's chat history."""
    case = get_object_or_404(PatientCase, pk=case_id)
    query = (request.POST.get("content") or "").strip()

    if not query:
        messages.error(request, "Message cannot be empty.")
        return redirect("cases:detail", case_id=case.id)

    ChatMessage.objects.create(
        patient_case=case,
        sender=ChatMessage.SENDER_CLINICIAN,
        content=query,
    )
    reply = chatbot.process_query(query, case)
    ChatMessage.objects.create(
        patient_case=case,
        sender=ChatMessage.SENDER_BOT,
        content=reply,
    )
    return HttpResponseRedirect(reverse("cases:detail", args=[case.id]) + "#chat")
