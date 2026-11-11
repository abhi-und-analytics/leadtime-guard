"""AI extractor: one structured LLM call per email (free providers: OpenCode CLI, Gemini, Ollama, Groq).

The model only READS: it copies the date words exactly and gives the sentence that proves them.
It never converts dates or decides the risk - fixed rules do that afterwards.
If the evidence sentence is not found in the email, we ask once more, then flag it for a human.
"""

from ..emails import Email
from ..llm.client import get_client, parse
from ..llm.cost import Usage
from ..schema import SupplierUpdate
from .grounding import is_grounded

SYSTEM = """You read supplier emails about equipment orders for a data-centre construction project.
Return the facts as JSON. Rules:
1. promised_date_text: the CURRENT promised date for delivery or hand-over of the WHOLE order, copied EXACTLY as
   written (e.g. "CW 6", "Q2 2027", "27.01.2027", "03/02/2027"). Never convert, calculate or reformat dates.
2. Ignore: dates in quoted earlier emails (lines starting with ">"), old dates that were superseded, and FAT/test dates.
3. Partial shipment: use the date of the LAST delivery that completes the order, and set partial_shipment = true.
4. date_basis: "on_site" = delivery to our site; "fca_handover" = ready for collection at the supplier's works,
   FCA or FOB hand-over; "ex_works" = EXW; "port_arrival" = ETA at a port (e.g. CIF Hamburg); otherwise "unknown".
5. date_status: "confirmed" if the supplier says confirmed; "tentative" for expect / planned / estimate / tentatively;
   "conditional" if the date depends on something ("subject to ..."); otherwise "unknown".
6. delay_notice = true if the supplier reports a delay or a later date. force_majeure = true only if the email says
   force majeure. fat_failed = true if the factory acceptance test failed or was missed.
7. If the email gives no date, promised_date_text = null.
8. evidence_quote: copy the ONE sentence that supports promised_date_text (or the delay / force majeure / FAT
   statement if there is no date) word for word from the email.
9. Never guess. Use null or "unknown" when something is not stated."""


class LLMExtractor:
    def __init__(self):
        self.client, self.settings = get_client()
        self.usage = Usage()

    def extract(self, email: Email) -> tuple[SupplierUpdate, bool]:
        """Returns (update, grounded)."""
        text = email.text_for_model()
        update, _ = parse(self.client, self.settings, self.usage, SupplierUpdate, system=SYSTEM, user_text=text,
                          max_tokens=4000)
        if is_grounded(update.evidence_quote, email.body):
            return update, True
        retry = SYSTEM + "\n\nYour previous evidence_quote was NOT found in the email. Copy it word for word."
        update, _ = parse(self.client, self.settings, self.usage, SupplierUpdate, system=retry, user_text=text,
                          max_tokens=4000)
        return update, is_grounded(update.evidence_quote, email.body)
