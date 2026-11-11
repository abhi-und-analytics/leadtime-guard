"""End to end, offline (no AI needed): emails -> extraction -> rules -> report, plus the evaluation."""

from leadtime_guard.emails import load_emails, without_quoted_text
from leadtime_guard.evaluate import evaluate, expected_risk
from leadtime_guard.extract.baseline import extract
from leadtime_guard.pipeline import run


def test_quoted_text_is_removed():
    assert "CW 5" not in without_quoted_text("New date CW 9.\n\n> On Fri, Klaus wrote:\n> CW 5 is confirmed.")


def test_baseline_reads_a_simple_email():
    e = next(m for m in load_emails() if m.email_id == "E03")
    u = extract(e)
    assert u.po_number == "PO-24003" and u.promised_date_text == "CW 6" and u.date_basis == "fca_handover"


def test_answer_key_has_red_amber_and_green():
    counts = expected_risk().rag.value_counts()
    assert counts["RED"] == 4 and counts["AMBER"] == 10 and counts["GREEN"] == 11


def test_offline_pipeline_end_to_end():
    df, drafts, unmatched, paths = run("offline", log=lambda *a, **k: None)
    assert len(df) == 25 and not unmatched
    assert set(df.rag) <= {"RED", "AMBER", "GREEN"}
    assert paths["xlsx"].exists() and len(drafts) == (df.rag != "GREEN").sum()


def test_evaluation_runs_and_finds_baseline_misses():
    run("offline", log=lambda *a, **k: None)
    res = evaluate("offline")
    assert res["rag"]["risky_items"] == 14
    assert res["rag"]["missed_risks"] >= 1          # the baseline falls for the superseded-date / partial-shipment traps
