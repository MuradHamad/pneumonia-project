"""ChatBot service — placeholder.

Returns a canned response that references the case so the UI flow
(prompt in → bot reply saved) works end-to-end before real RAG is wired.
Phase 12 replaces this with an embedding + LLM implementation; the
process_query() signature stays the same.
"""
from __future__ import annotations


def process_query(query: str, case) -> str:
    """Generate a bot reply for a clinician query on a specific case.

    Args:
        query: Clinician's free-text prompt.
        case: PatientCase instance.

    Returns:
        Plain-text reply that references the case context.
    """
    if case.has_pneumonia is True:
        finding = "Severe pneumonia" if case.is_severe else "Non-severe pneumonia"
        diag_pct = f"{case.diag_probability * 100:.1f}%" if case.diag_probability is not None else "unknown"
        context = f"{finding} (probability {diag_pct})"
    elif case.has_pneumonia is False:
        diag_pct = f"{case.diag_probability * 100:.1f}%" if case.diag_probability is not None else "unknown"
        context = f"No pneumonia (probability {diag_pct})"
    else:
        context = "pending diagnosis"

    return (
        f"[Placeholder] Based on case #{case.id} ({context}), "
        f"here is a response to: \"{query.strip()}\""
    )
