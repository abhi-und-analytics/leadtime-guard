"""Tests: grounding check and evaluation metrics."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from evals.harness import rag_metrics  # noqa: E402
from leadtime_guard.extract.grounding import is_grounded  # noqa: E402

EMAIL = "Dear team,\nthe equipment will be ready for collection\nat our Milan works in CW 6.\nBest regards"


def test_quote_found_across_line_breaks():
    assert is_grounded("ready for collection at our Milan works in CW 6.", EMAIL)


def test_invented_quote_is_not_grounded():
    assert not is_grounded("Delivery to site on 22 Feb 2027.", EMAIL)


def test_empty_quote_is_not_grounded():
    assert not is_grounded("", EMAIL)


def test_missed_risk_rate_counts_green_for_risky_items():
    m = rag_metrics(["red", "amber", "green", "green"], ["red", "green", "green", "amber"])
    assert m["missed_risks"] == 1 and m["missed_risk_rate_%"] == 50.0
    assert m["false_alarm_rate_%"] == 50.0


def test_confusion_matrix_has_all_three_classes():
    m = rag_metrics(["green"], ["green"])
    assert list(m["confusion_matrix"].index) == ["green", "amber", "red"]
