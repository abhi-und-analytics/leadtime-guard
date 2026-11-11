"""The structure the AI must return for every supplier email (validated with Pydantic)."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class SupplierUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")   # no extra keys allowed -> additionalProperties: false

    po_number: Optional[str] = Field(description="Purchase order number, e.g. PO-24003")
    promised_date_text: Optional[str] = Field(
        description="The CURRENT promised delivery or hand-over date, copied EXACTLY as written (e.g. 'CW 6', "
                    "'Q2 2027', '27.01.2027'). null if the email gives no date.")
    date_basis: Literal["on_site", "fca_handover", "ex_works", "port_arrival", "unknown"] = Field(
        description="What the date refers to: delivery to our site / ready for collection at supplier works or "
                    "FOB/FCA hand-over / ex works / arrival at a port / unknown")
    date_status: Literal["confirmed", "tentative", "conditional", "unknown"]
    delay_notice: bool = Field(description="True if the supplier reports a delay or a later date than before")
    force_majeure: bool
    fat_failed: bool = Field(description="True if the factory acceptance test (FAT) failed or was missed")
    partial_shipment: bool
    evidence_quote: str = Field(description="The one sentence from the email that supports the answer, copied word for word")
