"""Grounding check (reused from the AI Data Room project).

The evidence quote the model returns must appear in the email body. If it does not,
the value may be invented, so it is retried once and then flagged for a human.
"""

import re


def norm_text(s) -> str:
    """Lower case and single spaces, so line breaks and double spaces don't break the comparison."""
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def is_grounded(quote, source_text) -> bool:
    """True if the (non-empty) quote appears in the source text after normalising both."""
    if quote is None or not str(quote).strip():
        return False
    return norm_text(quote) in norm_text(source_text)
