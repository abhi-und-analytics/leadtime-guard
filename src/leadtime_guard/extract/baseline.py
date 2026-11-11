"""Offline BASELINE extractor: simple keyword and regex rules, no AI.

Why it exists: (1) the whole project runs without any AI provider, and (2) it is the yardstick for the AI.
It takes the FIRST date it finds, so it falls for traps such as superseded dates and partial shipments.
The evaluation shows exactly where the AI does better.
"""

import re

from ..emails import Email, without_quoted_text
from ..normalise.dates import MONTH_RE
from ..schema import SupplierUpdate

DATE_PATTERNS = [
    r"\b(?:CW|KW|calendar week)\s*\d{1,2}(?:\s*/?\s*\d{4})?",
    r"\bQ[1-4]\s*\d{4}",
    rf"\b(?:early|mid|late|end of)\s+(?:{MONTH_RE})\s+\d{{4}}",
    rf"\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{MONTH_RE})\s+\d{{4}}",
    r"\b\d{1,2}[./]\d{1,2}[./]\d{4}\b",
]
DATE_RE = re.compile("|".join(f"(?:{p})" for p in DATE_PATTERNS), re.I)


def _sentences(text: str):
    for line in text.splitlines():
        for s in re.split(r"(?<=[.!?])\s+", line.strip()):
            if s:
                yield s


def extract(email: Email) -> SupplierUpdate:
    body = without_quoted_text(email.body)
    low = body.lower()
    po = re.search(r"\bPO-\d{5}\b", email.subject + " " + body)
    m = DATE_RE.search(body)                                   # first date in the email
    date_text = m.group(0).strip() if m else None
    evidence = next((s for s in _sentences(body) if date_text and date_text in s), None)

    if re.search(r"collection|ready at our|works|\bfob\b|\bfca\b|loaded|ex works", low):
        basis = "fca_handover"
    elif re.search(r"\beta\b.*\bport\b|\bcif\b", low):
        basis = "port_arrival"
    elif re.search(r"to (?:your )?(?:\w+ )?site|delivered to site", low):
        basis = "on_site"
    else:
        basis = "unknown"
    if "subject to" in low:
        status = "conditional"
    elif re.search(r"tentativ|expect|planned|estimate", low):
        status = "tentative"
    elif "confirm" in low and "unable to confirm" not in low and "cannot be confirmed" not in low:
        status = "confirmed"
    else:
        status = "unknown"
    fm = "force majeure" in low
    fat = bool(re.search(r"(fat|acceptance test)[^.]*(not passed|failed|missed)", low))
    delay = bool(re.search(r"delay|late|moved|rolled|unable to confirm|cannot be confirmed|revised", low))
    partial = "partial" in low
    if evidence is None:   # no date: use the sentence that explains why
        key = re.compile(r"force majeure|unable to confirm|not passed|failed|delay", re.I)
        evidence = next((s for s in _sentences(body) if key.search(s)), next(_sentences(body), ""))
    return SupplierUpdate(po_number=po.group(0) if po else None, promised_date_text=date_text, date_basis=basis,
                          date_status=status, delay_notice=delay, force_majeure=fm, fat_failed=fat,
                          partial_shipment=partial, evidence_quote=evidence)
