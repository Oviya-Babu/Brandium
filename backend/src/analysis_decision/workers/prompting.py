"""Shared prompt-building and parsing helpers for evidence-extraction
workers (text_worker.py, image_worker.py) — no business logic beyond
string assembly and UUID parsing."""
from __future__ import annotations

import uuid

from src.brand_governance.domain.models import Assertion


def build_judgment_system_prompt(assertions: list[Assertion]) -> str:
    assertion_lines = "\n".join(f"- id={a.id}: {a.content}" for a in assertions)
    return (
        "You judge how well a piece of marketing/brand content aligns with a specific set of "
        "brand identity assertions. For each assertion below, decide whether the content is "
        "'aligned', 'partially_aligned', or 'misaligned' with it, and how confident you are "
        "(0-1). If the content simply doesn't contain enough material to judge a given "
        "assertion (e.g. it's too short, or about an unrelated topic), list that assertion's "
        "id in no_signal_assertion_ids instead of guessing — an absence of signal is never a "
        "negative judgment. Judge only the assertions listed; do not invent new ones, and do "
        "not comment on anything the content does well or poorly outside of them.\n\n"
        f"Assertions:\n{assertion_lines}"
    )


def safe_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        return None
