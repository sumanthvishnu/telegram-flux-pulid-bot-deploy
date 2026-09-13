"""Minors / underage hard-block only. No generic NSFW filter."""

from __future__ import annotations

import re

_BLOCK = re.compile(
    r"\b("
    r"child|children|kid|kids|toddler|infant|baby|babies|"
    r"minor|minors|underage|under\s*-?\s*age|"
    r"preteen|pre-teen|teen\s*girl|teen\s*boy|"
    r"schoolgirl|schoolboy|loli|shota|pedophil|pedo\b|"
    r"\d{1,2}\s*(y/?o|yrs?|years?\s*old)|"
    r"(eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen)\s*year"
    r")\b",
    re.IGNORECASE,
)


def blocks_minors(prompt: str) -> str | None:
    """Return a user-facing reason if the prompt must be rejected, else None."""
    if not prompt or not prompt.strip():
        return None
    if _BLOCK.search(prompt):
        return (
            "Blocked: prompts involving minors / underage are not allowed. "
            "Adult content is fine — rephrase without any underage reference."
        )
    return None
