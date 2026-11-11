"""Turn a supplier's date words ("CW 6", "Q2 2027", "early March 2027", "27.01.2027") into a real date,
and then into an on-site date. These are FIXED RULES (config/project.yaml), not AI: the same text always
gives the same date, and every rule is written down in docs/assumptions.md.
"""

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from .. import config

MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTHS.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})
MONTH_RE = "|".join(sorted(MONTHS, key=len, reverse=True))


@dataclass
class ParsedDate:
    value: Optional[date]          # None if no date or ambiguous
    precision: Optional[str]       # day | week | month_part | quarter | None
    ambiguous: bool = False        # e.g. "03/02/2027": 3 Feb or 2 Mar? Never guessed.
    note: str = ""


def _week_friday(year: int, week: int) -> date:
    weekday = int(config.project()["calendar_week"]["map_to_weekday"])
    return date.fromisocalendar(year, week, weekday)


def parse_date_text(text: Optional[str], email_date: date) -> ParsedDate:
    """Parse the supplier's exact date words. Returns ParsedDate(value=None) if there is no usable date."""
    if not text or not str(text).strip():
        return ParsedDate(None, None, note="no date given")
    t = str(text).strip()

    # 1) Calendar week: "CW 6", "KW 9", "week 26 2027", "CW 9 / 2027"
    m = re.search(r"\b(?:CW|KW|calendar week|week)\s*(\d{1,2})(?:\s*(?:/|of|,)?\s*(\d{4}))?", t, re.I)
    if m:
        week = int(m.group(1))
        year = int(m.group(2)) if m.group(2) else email_date.year
        if not m.group(2):   # missing year: if that week is long past, it means next year
            if _safe_week(year, week) is None or _safe_week(year, week) < email_date - timedelta(weeks=4):
                year += 1
        fri = _safe_week(year, week)
        if fri is None:
            return ParsedDate(None, None, note=f"week {week} does not exist in {year}")
        return ParsedDate(config.roll_forward(fri), "week", note=f"Friday of ISO week {week}/{year}")

    # 2) Quarter: "Q2 2027"
    m = re.search(r"\bQ([1-4])\s*/?\s*(\d{4})", t, re.I)
    if m:
        q, year = int(m.group(1)), int(m.group(2))
        last = date(year, q * 3, calendar.monthrange(year, q * 3)[1])
        return ParsedDate(config.roll_backward(last), "quarter", note=f"last working day of Q{q} {year}")

    # 3) Part of a month: "early March 2027", "mid June 2027", "late March 2027", "end of May 2027"
    m = re.search(rf"\b(early|beginning of|mid|middle of|late|end of)\s+({MONTH_RE})\.?\s+(\d{{4}})", t, re.I)
    if m:
        part, month, year = m.group(1).lower(), MONTHS[m.group(2).lower()], int(m.group(3))
        rule = config.project()["month_part"]
        key = "early" if part in ("early", "beginning of") else "mid" if part in ("mid", "middle of") else "late"
        if rule[key] == "last_working_day":
            d = config.roll_backward(date(year, month, calendar.monthrange(year, month)[1]))
        else:
            d = config.roll_forward(date(year, month, int(rule[key])))
        return ParsedDate(d, "month_part", note=f"{key} {calendar.month_name[month]} {year}")

    # 4) "25 January 2027", "1st February 2027", "January 25, 2027"
    m = re.search(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\.?\s+({MONTH_RE})\.?,?\s+(\d{{4}})", t, re.I)
    if m:
        return _day(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))
    m = re.search(rf"\b({MONTH_RE})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})", t, re.I)
    if m:
        return _day(int(m.group(3)), MONTHS[m.group(1).lower()], int(m.group(2)))

    # 5) ISO "2027-01-25"
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", t)
    if m:
        return _day(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    # 6) German style "27.01.2027" (day.month.year is unambiguous in this format)
    m = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b", t)
    if m:
        return _day(int(m.group(3)), int(m.group(2)), int(m.group(1)))

    # 7) Slash dates "18/02/2027" (day must be > 12) or "03/02/2027" (ambiguous -> flag, never guess)
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", t)
    if m:
        a, b, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if a <= 12 and b <= 12 and a != b:
            return ParsedDate(None, None, ambiguous=True, note=f"'{m.group(0)}' could be dd/mm or mm/dd")
        if a > 12:
            return _day(year, b, a)
        if b > 12:
            return _day(year, a, b)
        return _day(year, b, a)
    return ParsedDate(None, None, note=f"could not read a date from '{t}'")


def _safe_week(year, week):
    try:
        return _week_friday(year, week)
    except ValueError:
        return None


def _day(year, month, day_) -> ParsedDate:
    try:
        return ParsedDate(date(year, month, day_), "day")
    except ValueError:
        return ParsedDate(None, None, note="impossible calendar date")


def to_on_site(supplier_date: Optional[date], basis: str, origin_region: str) -> Optional[date]:
    """Supplier date -> on-site date, using the Incoterm basis rules in config/project.yaml.
    on_site: as given. fca_handover / ex_works / unknown: + transit + receiving. port_arrival: + port-to-site + receiving."""
    if supplier_date is None:
        return None
    cfg = config.project()
    rule = cfg["date_basis_rules"].get(basis or "unknown", cfg["date_basis_rules"]["unknown"])
    d = supplier_date
    if rule["add_transit"]:
        d = config.add_calendar_days(d, int(cfg["transit_days"][origin_region]))
    if rule["add_port_to_site"]:
        d = config.add_calendar_days(d, int(cfg["port_to_site_days"]))
    if rule["add_receiving"]:
        d = config.add_working_days(d, int(cfg["receiving_buffer_wd"]))
    return d
