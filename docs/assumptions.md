# Assumptions

LeadTime Guard is a portfolio project. Everything below is a **stated assumption**, written down before the first evaluation run so the results can't be tuned afterwards.

## Data
- **All data is synthetic.** FRA-DC1 is a fictional 2-hall data centre near Frankfurt am Main. All supplier names end in "(fictional)" and all email domains use the reserved `.example` ending. No real company, supplier or project data is used.
- **Lead times** in the register are set inside reference ranges from public 2025–2026 industry sources (PO to ex-works, weeks): HV/MV transformer 75–130, MV switchgear 52–104, LV switchboard 40–85, diesel generator 70–110, UPS 30–48, chiller 30–60. Busway, CRAH, dry coolers, BMS/EPMS, fuel systems and CDUs have **no sourced 2025–26 range**; their values are my assumption.
- **As-of date:** Monday **14 December 2026** (ISO week 51). This forces year-boundary cases: 2026 has **53 ISO weeks**, and CW 53/2026 ends on Friday 1 January 2027, a public holiday.

## Dates
- **ROS (required on site)** = the date an item must be on site so the next activity (installation) can start, minus a receiving buffer. The buffer convention is my assumption.
- **A calendar week ("CW 6", "KW 6")** maps to the **Friday** of that ISO week, rolled forward to the next working day if that Friday is a holiday.
- **Missing year on a week:** if the week lies more than 4 weeks before the email's own week, the next year is used.
- **A quarter ("Q2 2027")** maps to its **last working day** and is always treated as **tentative**.
- **"Early / mid / late month"** maps to the 10th, the 20th and the last working day.
- **Ambiguous dd/mm dates** (both numbers ≤ 12, e.g. "03/04/2027") are **never guessed**; they are flagged for a human.
- **German "27.01.2027"** is always day.month.year. A slash date with one number above 12 ("18/02/2027") is unambiguous.
- **Several dates in one email:** the *current* promised date for the whole order counts. Superseded dates, FAT dates and dates in quoted earlier emails are ignored.
- **Partial shipment:** the date of the *last* delivery counts, because the item is only complete then.
- **Newest email wins:** if an item has several emails, the most recent one is used. Items without a new email keep the register's forecast and last-update date.
- **Working days** exclude weekends and the public holidays of **Hesse** for 2026–2027 (see `config/project.yaml`; Easter-based dates are double-checked in `scripts/check_register.py`).

## Supplier date → on-site date (Incoterms)
- **DAP / DDP to site:** the supplier's date is the on-site date. No transit is added.
- **FCA / FOB / EXW:** the supplier's date is a hand-over or ex-works date. Transit + receiving buffer are added.
- **CIF port:** the supplier's date is the port arrival. Port-to-site time + receiving buffer are added.
- **Transit times** (calendar days, assumptions): EU road 7, UK road 9, Asia sea 56 (+4 days port to site). **Receiving buffer:** 2 working days.
- **Unknown basis:** treated like ex-works (conservative) and flagged.

## Risk rules (see `config/risk_rules.yaml`)
- **The green / amber / red thresholds are this project's own assumption, not an industry standard.** No published AACE, PMI or CII numeric thresholds were found; real projects set them per contract.
- **Red:** the item's shortfall against ROS is larger than the successor's float (the milestone moves), OR a delay / force-majeure notice has no revised date, OR FAT failed or was missed with no new date.
- **Amber:** float under 20 working days, OR a tentative / conditional / quarter-level date within 26 weeks of ROS, OR a stale update (more than 14 days for class A, 30 days for B/C), OR an unresolved conflict or ambiguous date.
- **Green:** everything that is not red or amber (float of 20 working days or more, no warning signs). A tentative date more than 26 weeks before ROS stays green but should be re-checked.
- **Evidence missing:** if the AI's evidence sentence is not found in the email (after one retry), the item becomes amber and a person must check it.

## Human in the loop
- **Nothing is sent automatically.** Every chaser or escalation email is a draft that a person approves or rejects; each decision is logged.
- **Force majeure:** the tool writes only an internal note telling a human to check notice deadlines and contract clauses. It never writes legal positions.

## What the evaluation does and does not prove
- The expected rating in the answer key comes from **my rules applied to the true facts**. So the evaluation measures whether the pipeline **reads supplier emails correctly**, not whether my thresholds are the right ones for a real project.
