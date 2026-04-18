"""ChatBot service — placeholder.

Returns a canned response that references the case so the UI flow
(prompt in → bot reply saved) works end-to-end before real RAG is wired.
Phase 12 replaces this with an embedding + LLM implementation; the
`process_query()` signature will stay the same.
"""
from __future__ import annotations


def process_query(query: str, case) -> str:
    """Generate a bot reply for a clinician query on a specific case.

    Args:
        query: Clinician's free-text prompt.
        case: PatientCase instance (attributes: id, risk_class, severity_score, status).

    Returns:
        Plain-text reply that at least references the case context.
    """
    risk = case.risk_class or "not yet determined"
    severity = (
        f"{case.severity_score:.2f}" if case.severity_score is not None else "n/a"
    )
    return (
        f"[Placeholder] Based on case #{case.id} (Risk Class {risk}, "
        f"severity {severity}), here is a response to: \"{query.strip()}\""
    )
