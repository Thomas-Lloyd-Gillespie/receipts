"""Deterministic quote checks.

No model decides whether a quote is real. A quote counts only if it appears
word for word in the text it claims to come from, after evening out
whitespace and typographic quote marks and dashes. Case and wording must match.
"""

from __future__ import annotations

import hashlib
import re

_TYPOGRAPHY = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        " ": " ",
    }
)


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.translate(_TYPOGRAPHY)).strip()


def found(quote: str, text: str) -> bool:
    q = norm(quote)
    return bool(q) and q in norm(text)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
