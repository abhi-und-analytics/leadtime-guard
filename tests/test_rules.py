"""Risk rules: red, amber and green cases."""

from datetime import date

from leadtime_guard.rules.engine import ItemUpdate, assess

REG = {"item_id": "EQ-X", "ros_date": "2027-02-15", "successor_float_wd": "10", "milestone_id": "M1",
       "current_forecast_on_site": "2027-01-04", "last_update_date": "2026-12-10", "date_status": "confirmed",
       "criticality_class": "A"}
TODAY = date(2026, 12, 14)


def upd(**kw):
    base = dict(email_id="E", email_date=date(2026, 12, 10), on_site=date(2027, 1, 4), precision="day",
                date_text="4 January 2027", date_status="confirmed")
    base.update(kw)
    return ItemUpdate(**base)


def test_green_when_enough_float():
    assert assess(REG, upd(), TODAY).rag == "green"


def test_amber_when_float_below_20_working_days():
    a = assess(REG, upd(on_site=date(2027, 1, 25)), TODAY)
    assert a.rag == "amber" and a.float_wd == 15


def test_red_when_late_beyond_successor_float():
    a = assess(REG, upd(on_site=date(2027, 3, 5)), TODAY)
    assert a.rag == "red" and a.milestone_moves


def test_late_but_absorbed_by_successor_float_is_amber():
    assert assess(REG, upd(on_site=date(2027, 2, 19)), TODAY).rag == "amber"


def test_delay_without_date_is_red():
    assert assess(REG, upd(on_site=None, date_text=None, delay_notice=True), TODAY).rag == "red"


def test_force_majeure_gets_internal_note_only():
    a = assess(REG, upd(on_site=None, date_text=None, force_majeure=True, delay_notice=True), TODAY)
    assert a.rag == "red" and a.action == "internal_note"


def test_ambiguous_date_is_amber():
    assert assess(REG, upd(on_site=None, ambiguous=True, date_text="03/02/2027"), TODAY).rag == "amber"


def test_stale_register_item_is_amber():
    reg = dict(REG, last_update_date="2026-11-20")
    assert assess(reg, None, TODAY).rag == "amber"


def test_missing_evidence_is_amber():
    assert assess(REG, upd(grounded=False), TODAY).rag == "amber"
