"""Draft emails for amber / red items. They are DRAFTS: a person approves, edits or rejects every one
(config/risk_rules.yaml: auto_send = false). Force majeure gets an internal note only, never a reply."""

from datetime import date


def make_draft(item: dict, a, update) -> dict:
    """Return {item_id, kind, to, subject, body} or None for green items."""
    if a.action == "none":
        return None
    contact = item["supplier_contact"]
    po, desc = item["po_number"], item["description"]
    ros = date.fromisoformat(item["ros_date"]).strftime("%d %b %Y")
    reasons = "; ".join(a.reasons)
    if a.action == "internal_note":
        return dict(item_id=item["item_id"], kind="internal_note", to="project-manager@fra-dc1.example",
                    subject=f"[Internal] Force majeure notice on {po} - legal check needed",
                    body=(f"Supplier {item['supplier']} sent a force majeure notice for {desc} ({po}).\n"
                          f"Required on site: {ros}. Milestone: {item['milestone_id']}.\n\n"
                          "Action for a person: check the notice deadlines and contract clauses with legal before any "
                          "reply. LeadTime Guard does not write legal positions.\n"))
    if a.action == "escalation":
        return dict(item_id=item["item_id"], kind="escalation", to=contact,
                    subject=f"{po} - urgent: delivery risk for {desc}",
                    body=(f"Dear supplier team,\n\nyour latest update on {po} ({desc}) puts our project milestone "
                          f"{item['milestone_id']} at risk. We need this equipment on site by {ros}.\n\n"
                          "Please send within 2 working days:\n- a revised, dated delivery schedule\n"
                          "- your recovery options (e.g. expediting, partial shipment, resequencing)\n\n"
                          "We would also like to set up a short call this week.\n\nKind regards\n"
                          "Project Procurement, FRA-DC1\n"),
                    internal_note=f"Why: {reasons}. Options to discuss: paid expediting, partial shipment, "
                                  "temporary power, resequencing, alternative supplier.")
    if update and update.ambiguous:
        ask = (f"Your date '{update.date_text}' can be read in two ways (day/month or month/day). "
               "Could you please confirm the delivery date with the month written out (e.g. 3 February 2027)?")
    elif update is None:
        ask = ("We have not received an update for some time. Could you please send your current delivery date "
               "and the latest manufacturing schedule?")
    else:
        ask = (f"Could you please confirm '{update.date_text}' in writing with a dated factory slot letter or "
               "your latest manufacturing schedule?")
    return dict(item_id=item["item_id"], kind="chaser", to=contact,
                subject=f"{po} - please confirm a dated slot",
                body=(f"Dear supplier team,\n\nthank you for your update on {po} ({desc}). "
                      f"To protect our required-on-site date of {ros}, we need one more step from you. {ask}\n\n"
                      "Thank you and kind regards\nProject Procurement, FRA-DC1\n"),
                internal_note=f"Why: {reasons}.")
