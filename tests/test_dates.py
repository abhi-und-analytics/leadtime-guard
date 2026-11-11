"""Date rules: calendar weeks, quarters, month parts, date formats, holidays and Incoterm basis."""

from datetime import date

from leadtime_guard.normalise.dates import parse_date_text, to_on_site

DEC = date(2026, 12, 10)


def test_calendar_week_without_year_means_next_year():
    assert parse_date_text("CW 6", DEC).value == date(2027, 2, 12)        # Friday of ISO week 6/2027


def test_german_kw_works_too():
    assert parse_date_text("KW 9", DEC).value == date(2027, 3, 5)


def test_cw53_rolls_past_new_year_holiday():
    # ISO week 53 of 2026 ends on Friday 1 Jan 2027, a public holiday -> next working day
    assert parse_date_text("CW 53", date(2026, 12, 4)).value == date(2027, 1, 4)


def test_quarter_is_last_working_day_and_marked():
    p = parse_date_text("Q1 2027", DEC)
    assert p.value == date(2027, 3, 31) and p.precision == "quarter"


def test_month_parts():
    assert parse_date_text("early March 2027", DEC).value == date(2027, 3, 10)
    assert parse_date_text("late March 2027", DEC).value == date(2027, 3, 31)


def test_date_formats():
    assert parse_date_text("27.01.2027", DEC).value == date(2027, 1, 27)
    assert parse_date_text("18/02/2027", DEC).value == date(2027, 2, 18)
    assert parse_date_text("25 January 2027", DEC).value == date(2027, 1, 25)


def test_ambiguous_slash_date_is_never_guessed():
    p = parse_date_text("03/02/2027", DEC)
    assert p.value is None and p.ambiguous


def test_no_date():
    assert parse_date_text(None, DEC).value is None


def test_fca_date_gets_transit_and_receiving():
    # CW 6 (Fri 12 Feb) + 7 days EU road = Fri 19 Feb, + 2 working days = Tue 23 Feb
    assert to_on_site(date(2027, 2, 12), "fca_handover", "EU-road") == date(2027, 2, 23)


def test_site_date_stays_as_it_is():
    assert to_on_site(date(2027, 1, 25), "on_site", "EU-road") == date(2027, 1, 25)


def test_arrival_over_easter_rolls_forward():
    # FOB 29 Jan + 56 days = Good Friday 26 Mar 2027; Easter Monday too -> Tue 30 Mar + 2 working days = Thu 1 Apr
    assert to_on_site(date(2027, 1, 29), "fca_handover", "Asia-sea") == date(2027, 4, 1)
