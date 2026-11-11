"""Evaluation helpers (reused from the AI Data Room project, extended for risk ratings).

Full evaluation (run_eval.py) comes on Day 9. These helpers are ready now.
Key metric: MISSED-RISK RATE = truly amber/red items that the pipeline rated green / all truly amber/red items.
"""

import pandas as pd

RAG_ORDER = ["green", "amber", "red"]


def field_accuracy(pred: pd.DataFrame, key: pd.DataFrame, fields, on="email_id") -> pd.DataFrame:
    """Share of exact matches per field (after joining prediction and answer key on `on`)."""
    m = key.merge(pred, on=on, suffixes=("_key", "_pred"))
    rows = [{"field": f, "accuracy_%": round((m[f + "_key"].astype(str) == m[f + "_pred"].astype(str)).mean() * 100, 1)}
            for f in fields]
    return pd.DataFrame(rows)


def rag_metrics(true_rag, pred_rag) -> dict:
    """Missed-risk rate, red recall, false-alarm rate, and a 3x3 confusion matrix (counts)."""
    t = pd.Series(list(true_rag), name="true").str.lower()
    p = pd.Series(list(pred_rag), name="predicted").str.lower()
    risky = t.isin(["amber", "red"])
    missed = (risky & (p == "green")).sum()
    red = t == "red"
    green = t == "green"
    return {
        "risky_items": int(risky.sum()),
        "missed_risks": int(missed),
        "missed_risk_rate_%": round(missed / risky.sum() * 100, 1) if risky.sum() else None,
        "red_recall_%": round(((p == "red") & red).sum() / red.sum() * 100, 1) if red.sum() else None,
        "false_alarm_rate_%": round(((p != "green") & green).sum() / green.sum() * 100, 1) if green.sum() else None,
        "confusion_matrix": pd.crosstab(t, p).reindex(index=RAG_ORDER, columns=RAG_ORDER, fill_value=0),
    }
