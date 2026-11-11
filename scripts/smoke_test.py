"""Day 1 smoke test: one structured call to a FREE model (default: OpenCode CLI) with a Pydantic model.

Run:   python scripts/smoke_test.py
Pass:  it prints a parsed SmokeUpdate object, "grounded: True" and a usage line (cost EUR 0).
Switch provider: set LTG_PROVIDER=gemini, ollama (local, offline) or groq.
"""

import sys
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from leadtime_guard.extract.grounding import is_grounded  # noqa: E402
from leadtime_guard.llm.client import get_client, parse  # noqa: E402
from leadtime_guard.llm.cost import Usage  # noqa: E402


class SmokeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")   # -> additionalProperties: false
    po_number: Optional[str]
    promised_date_text: Optional[str]          # the supplier's EXACT words, e.g. "CW 6"
    date_basis: Literal["ex_works", "fca_handover", "port_arrival", "on_site", "unknown"]
    date_status: Literal["confirmed", "tentative", "conditional", "unknown"]
    evidence_quote: str                        # must appear word for word in the email


SYSTEM = """You read supplier emails about equipment orders for a construction project.
Rules:
1. Copy the promised date EXACTLY as written (for example "CW 6"). Never convert or calculate dates.
2. date_basis: where the date applies. "Ready for collection at our works" under FCA = fca_handover.
3. Ignore quoted earlier emails and signatures.
4. evidence_quote: copy the one sentence that contains the date, word for word.
5. If something is not stated, use null or "unknown". Never guess."""

EMAIL = """From: m.rossi@lombardia-quadri.example
Date: Thu, 10 Dec 2026 09:14:00 +0100
Subject: PO-24003 - MV switchgear lineup A - production update

Dear project team,
production of lineup A is progressing. Due to a delayed busbar delivery, the equipment will be
ready for collection at our Milan works in CW 6. FAT remains planned for CW 3.
This date is confirmed.
Best regards, Marco Rossi (fictional)"""


def main():
    client, settings = get_client()
    usage = Usage()
    print(f"Provider      : {settings['name']}  model: {settings['model'] or 'OpenCode default'}")
    update, response = parse(client, settings, usage, SmokeUpdate, system=SYSTEM, user_text=EMAIL, max_tokens=4000)
    print("Parsed object :", update)
    print("Finish reason :", response.choices[0].finish_reason)
    print("grounded      :", is_grounded(update.evidence_quote, EMAIL))
    print("Usage         :", usage.summary())


if __name__ == "__main__":
    main()
