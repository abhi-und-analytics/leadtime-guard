"""Builds the 23 synthetic supplier emails (data/emails/*.txt) and the human-checked answer key
(data/answer_key/extraction_key.csv). Every trap is described in the `trap` column. Run: python scripts/make_synthetic_emails.py"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]   # project folder
TO = "procurement@fra-dc1.example"
E = []  # (id, from, date, subject, body, truth dict, trap)

def add(eid, frm, dt, subj, body, trap, po, text, basis, status, delay=False, fm=False, fat=False, partial=False, quote=""):
    E.append(dict(email_id=eid, frm=frm, date=dt, subject=subj, body=body.strip("\n"), trap=trap,
                  truth=dict(po_number=po, promised_date_text=text, date_basis=basis, date_status=status,
                             delay_notice=delay, force_majeure=fm, fat_failed=fat, partial_shipment=partial,
                             evidence_quote=quote)))

add("E01", "k.becker@nordwerk-trafo.example", "Mon, 07 Dec 2026 10:12:00 +0100",
    "PO-24001 Transformer T1 - delivery update", """
Dear Sir or Madam,

thank you for your patience. Our original plan of 11 January 2027 for transformer T1 has moved.
Delivery to your Frankfurt site is now confirmed for 25 January 2027.
The FAT will take place one week before shipment; the invitation follows.

Kind regards
Klaus Becker
Nordwerk Transformatoren GmbH (fictional)""",
    "superseded date: an older date appears first", "PO-24001", "25 January 2027", "on_site", "confirmed", delay=True,
    quote="Delivery to your Frankfurt site is now confirmed for 25 January 2027.")

add("E02", "k.becker@nordwerk-trafo.example", "Wed, 09 Dec 2026 15:40:00 +0100",
    "RE: PO-24002 Transformer T2 - revised delivery", """
Dear project team,

unfortunately our core steel supplier is late. Delivery of transformer T2 to site is now confirmed for CW 9 / 2027.
We apologise for the inconvenience and will share the updated test schedule shortly.

Best regards
Klaus Becker
Nordwerk Transformatoren GmbH (fictional)

> On Fri, 04 Dec 2026, Klaus Becker wrote:
> Delivery of T2 to your site in CW 5 is confirmed.""",
    "quoted older email contains an old date", "PO-24002", "CW 9 / 2027", "on_site", "confirmed", delay=True,
    quote="Delivery of transformer T2 to site is now confirmed for CW 9 / 2027.")

add("E03", "m.rossi@lombardia-quadri.example", "Thu, 10 Dec 2026 09:14:00 +0100",
    "PO-24003 - MV switchgear lineup A - production update", """
Dear project team,

production of lineup A is progressing. Due to a delayed busbar delivery, the equipment will be ready for collection at our Milan works in CW 6.
FAT remains planned for CW 3. This date is confirmed.

Best regards, Marco Rossi (fictional)
Lombardia Quadri S.p.A. (fictional)""",
    "works date (FCA), not a site date; week without year", "PO-24003", "CW 6", "fca_handover", "confirmed", delay=True,
    quote="the equipment will be ready for collection at our Milan works in CW 6.")

add("E04", "m.rossi@lombardia-quadri.example", "Thu, 10 Dec 2026 09:20:00 +0100",
    "PO-24004 - MV switchgear lineup B", """
Dear project team,

lineup B will be ready for collection at our Milan works on 27.01.2027. This date is confirmed.

Best regards, Marco Rossi (fictional)""",
    "German date format dd.mm.yyyy", "PO-24004", "27.01.2027", "fca_handover", "confirmed",
    quote="lineup B will be ready for collection at our Milan works on 27.01.2027.")

add("E05", "s.wagner@rheintal-sa.example", "Mon, 07 Dec 2026 11:02:00 +0100",
    "PO-24005 LV switchboard Hall 1 A-side", """
Hello,

we expect delivery to site in Q1 2027, subject to final drawing approval from your side.
Please send the approved drawings as soon as possible.

Regards
Stefan Wagner, Rheintal Schaltanlagen AG (fictional)""",
    "quarter-level date + condition", "PO-24005", "Q1 2027", "on_site", "conditional",
    quote="we expect delivery to site in Q1 2027, subject to final drawing approval from your side.")

add("E06", "s.wagner@rheintal-sa.example", "Mon, 07 Dec 2026 11:05:00 +0100",
    "PO-24006 LV switchboard Hall 1 B-side", """
Hello,

delivery to site: 18/02/2027 (confirmed).

Regards
Stefan Wagner, Rheintal Schaltanlagen AG (fictional)""",
    "slash date that is NOT ambiguous (18 > 12)", "PO-24006", "18/02/2027", "on_site", "confirmed",
    quote="delivery to site: 18/02/2027 (confirmed).")

add("E07", "orders@elbe-stromschienen.example", "Wed, 02 Dec 2026 08:30:00 +0100",
    "Order PO-24007 busway", """
Dear customer,

busway delivery to site is planned for 03/02/2027.

With kind regards
Order desk, Elbe Stromschienen GmbH (fictional)""",
    "ambiguous date 03/02/2027 (3 Feb or 2 Mar?)", "PO-24007", "03/02/2027", "on_site", "tentative",
    quote="busway delivery to site is planned for 03/02/2027.")

add("E08", "j.hughes@kestrel-power.example", "Fri, 04 Dec 2026 13:45:00 +0000",
    "PO-24008 generator sets 1-2", """
Hi team,

good news: sets 1-2 will be ready for collection at our Peterborough works in CW 53. This is confirmed.
FAT passed last week.

Cheers,
James Hughes
Kestrel Power Systems Ltd (fictional)""",
    "CW 53 / year boundary; Friday 1 Jan 2027 is a holiday; UK transit", "PO-24008", "CW 53", "fca_handover", "confirmed",
    quote="sets 1-2 will be ready for collection at our Peterborough works in CW 53.")

add("E09", "j.hughes@kestrel-power.example", "Tue, 08 Dec 2026 16:20:00 +0000",
    "PO-24009 generator sets 3-4 - delay", """
Hi team,

due to a shortage of alternators we are currently unable to confirm a collection date for sets 3-4.
We will revert with a revised schedule as soon as possible.

Regards,
James Hughes
Kestrel Power Systems Ltd (fictional)""",
    "delay notice WITHOUT a new date", "PO-24009", None, "fca_handover", "unknown", delay=True,
    quote="due to a shortage of alternators we are currently unable to confirm a collection date for sets 3-4.")

add("E10", "sales.eu@hanshin-pe.example", "Thu, 03 Dec 2026 07:55:00 +0800",
    "PO-24010 UPS Hall 1 A-side shipping", """
Dear customer,

UPS modules for Hall 1 A-side will be loaded FOB Ningbo on 8 January 2027. Vessel is booked.

Best regards
Hanshin Power Electronics Co., Ltd. (fictional)""",
    "FOB port date + 56 days sea transit", "PO-24010", "8 January 2027", "fca_handover", "confirmed",
    quote="UPS modules for Hall 1 A-side will be loaded FOB Ningbo on 8 January 2027.")

add("E11", "sales.eu@hanshin-pe.example", "Thu, 03 Dec 2026 08:05:00 +0800",
    "PO-24011 UPS Hall 1 B-side shipping", """
Dear customer,

the shipment for Hall 1 B-side has been rolled to the next vessel. New FOB date: 29 January 2027.

Best regards
Hanshin Power Electronics Co., Ltd. (fictional)""",
    "arrival falls on Easter holidays", "PO-24011", "29 January 2027", "fca_handover", "confirmed", delay=True,
    quote="New FOB date: 29 January 2027.")

add("E12", "sales.eu@hanshin-pe.example", "Thu, 03 Dec 2026 08:10:00 +0800",
    "PO-24012 battery cabinets ETA", """
Dear customer,

battery cabinets: ETA Hamburg port 19 March 2027 (CIF Hamburg).

Best regards
Hanshin Power Electronics Co., Ltd. (fictional)""",
    "port arrival date (CIF) + port-to-site", "PO-24012", "19 March 2027", "port_arrival", "confirmed",
    quote="battery cabinets: ETA Hamburg port 19 March 2027 (CIF Hamburg).")

add("E13", "c.martin@aquilon-cooling.example", "Fri, 04 Dec 2026 10:30:00 +0100",
    "PO-24013 chillers Hall 1 - FAT result", """
Dear project team,

the factory acceptance test for the Hall 1 chillers was not passed due to compressor vibration.
A new FAT date will be proposed after the root-cause analysis.

Kind regards
Claire Martin
Aquilon Cooling S.A.S. (fictional)""",
    "FAT failed and no new date", "PO-24013", None, "fca_handover", "unknown", fat=True,
    quote="the factory acceptance test for the Hall 1 chillers was not passed due to compressor vibration.")

add("E14", "project@nordic-air.example", "Tue, 08 Dec 2026 09:00:00 +0100",
    "PO-24014 CRAH units Hall 1", """
Hej,

CRAH units Hall 1: delivery to site in KW 9, confirmed.

Best regards
Nordic Air Handling AB (fictional)""",
    "German 'KW' without a year", "PO-24014", "KW 9", "on_site", "confirmed",
    quote="CRAH units Hall 1: delivery to site in KW 9, confirmed.")

add("E15", "project@nordic-air.example", "Tue, 08 Dec 2026 09:05:00 +0100",
    "PO-24015 dry coolers", """
Hej,

the dry coolers will be delivered to site early March 2027.

Best regards
Nordic Air Handling AB (fictional)""",
    "vague month-part date", "PO-24015", "early March 2027", "on_site", "unknown",
    quote="the dry coolers will be delivered to site early March 2027.")

add("E16", "pm@helix-controls.example", "Wed, 09 Dec 2026 14:10:00 +0100",
    "PO-24017 BMS/EPMS hardware", """
Dear all,

our previous estimate of 4 March 2027 has been superseded: delivery to site is now confirmed for 18 March 2027.

Best regards
Helix Controls GmbH (fictional)""",
    "superseded date appears first", "PO-24017", "18 March 2027", "on_site", "confirmed",
    quote="delivery to site is now confirmed for 18 March 2027.")

add("E17", "c.martin@aquilon-cooling.example", "Fri, 04 Dec 2026 10:40:00 +0100",
    "PO-24018 CDUs Hall 1", """
Dear project team,

the CDUs will be ready at our Lyon works in late March 2027, subject to receipt of your cooling-loop drawings.

Kind regards
Claire Martin
Aquilon Cooling S.A.S. (fictional)""",
    "month-part + condition, works date", "PO-24018", "late March 2027", "fca_handover", "conditional",
    quote="the CDUs will be ready at our Lyon works in late March 2027, subject to receipt of your cooling-loop drawings.")

add("E18", "k.becker@nordwerk-trafo.example", "Mon, 07 Dec 2026 10:20:00 +0100",
    "PO-24019 Transformer T3", """
Dear Sir or Madam,

for transformer T3 we currently expect delivery to site in Q2 2027.

Kind regards
Klaus Becker
Nordwerk Transformatoren GmbH (fictional)""",
    "quarter-level date", "PO-24019", "Q2 2027", "on_site", "tentative",
    quote="for transformer T3 we currently expect delivery to site in Q2 2027.")

add("E19", "m.rossi@lombardia-quadri.example", "Thu, 10 Dec 2026 09:30:00 +0100",
    "PO-24020 - MV switchgear lineup C", """
Dear project team,

the FAT for lineup C is planned for 26 May 2027 and the lineup will be ready for collection at our works on 10 June 2027.
Production slot confirmed.

Best regards, Marco Rossi (fictional)""",
    "FAT date appears before the delivery date", "PO-24020", "10 June 2027", "fca_handover", "confirmed",
    quote="the FAT for lineup C is planned for 26 May 2027 and the lineup will be ready for collection at our works on 10 June 2027.")

add("E20", "s.wagner@rheintal-sa.example", "Mon, 07 Dec 2026 17:00:00 +0100",
    "PO-24021 - Notice of force majeure", """
Dear Sir or Madam,

we hereby notify you of a force majeure event at our plant (flooding of the assembly hall).
The delivery date for the Hall 2 switchboard cannot be confirmed at this time.

Regards
Stefan Wagner, Rheintal Schaltanlagen AG (fictional)""",
    "force majeure, no date", "PO-24021", None, "on_site", "unknown", delay=True, fm=True,
    quote="we hereby notify you of a force majeure event at our plant (flooding of the assembly hall).")

add("E21", "sales.eu@hanshin-pe.example", "Thu, 03 Dec 2026 08:20:00 +0800",
    "PO-24023 UPS Hall 2", """
Dear customer,

the FOB date for the Hall 2 UPS remains tentatively 2 May 2027.

Best regards
Hanshin Power Electronics Co., Ltd. (fictional)""",
    "tentative date far from ROS (> 26 weeks)", "PO-24023", "2 May 2027", "fca_handover", "tentative",
    quote="the FOB date for the Hall 2 UPS remains tentatively 2 May 2027.")

add("E22", "c.martin@aquilon-cooling.example", "Fri, 04 Dec 2026 10:50:00 +0100",
    "PO-24024 chillers Hall 2", """
Dear project team,

the Hall 2 chillers will be ready for collection at our Lyon works in CW 26 2027. Confirmed.

Kind regards
Claire Martin
Aquilon Cooling S.A.S. (fictional)""",
    "week with year", "PO-24024", "CW 26 2027", "fca_handover", "confirmed",
    quote="the Hall 2 chillers will be ready for collection at our Lyon works in CW 26 2027.")

add("E23", "project@nordic-air.example", "Tue, 08 Dec 2026 09:10:00 +0100",
    "PO-24025 CRAH units Hall 2 - partial shipment", """
Hej,

we will make a partial shipment: 12 of 24 CRAH units delivered to site on 12 July 2027, the remaining 12 units on 23 August 2027.
Both dates are confirmed.

Best regards
Nordic Air Handling AB (fictional)""",
    "partial shipment: the LAST date completes the item", "PO-24025", "23 August 2027", "on_site", "confirmed", partial=True,
    quote="we will make a partial shipment: 12 of 24 CRAH units delivered to site on 12 July 2027, the remaining 12 units on 23 August 2027.")

out = ROOT / "data/emails"
for e in E:
    (out / f"{e['email_id']}.txt").write_text(
        f"From: {e['frm']}\nTo: {TO}\nDate: {e['date']}\nSubject: {e['subject']}\n\n{e['body']}\n", encoding="utf-8")
    assert e["truth"]["evidence_quote"].lower().replace("\n", " ") in e["body"].lower().replace("\n", " "), e["email_id"]
fields = ["email_id", "po_number", "promised_date_text", "date_basis", "date_status", "delay_notice", "force_majeure",
          "fat_failed", "partial_shipment", "evidence_quote", "trap"]
with open(ROOT / "data/answer_key/extraction_key.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for e in E:
        w.writerow({"email_id": e["email_id"], **{k: ("" if v is None else v) for k, v in e["truth"].items()}, "trap": e["trap"]})
print(len(E), "emails written")
