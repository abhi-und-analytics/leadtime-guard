"""Evaluate an extractor against the human-checked answer key.

    python -m leadtime_guard.evaluate --provider offline
    python -m leadtime_guard.evaluate --provider opencode     (after: python -m leadtime_guard.run --provider opencode)

The EXPECTED colour of each item comes from the answer key's true facts run through the same fixed rules.
So the evaluation measures whether the extractor READS the emails correctly - not whether my thresholds are right.
Key metric: missed-risk rate = truly amber/red items rated green, divided by all truly amber/red items.
"""

import argparse
import json
import sys

import pandas as pd

from .config import ROOT
from .emails import load_emails
from .normalise.dates import parse_date_text
from .pipeline import PROVIDERS, assess_all, load_register

sys.path.insert(0, str(ROOT))
from evals.harness import rag_metrics  # noqa: E402

BOOL = ["delay_notice", "force_majeure", "fat_failed", "partial_shipment"]


def load_key() -> list[dict]:
    key = pd.read_csv(ROOT / "data/answer_key/extraction_key.csv", dtype=str).fillna("")
    rows = []
    for r in key.to_dict("records"):
        x = {k: (r[k] if r[k] != "" else None) for k in ["email_id", "po_number", "promised_date_text", "date_basis",
                                                        "date_status", "evidence_quote"]}
        x.update({b: r[b] == "True" for b in BOOL})
        x["grounded"] = True
        rows.append(x)
    return rows


def expected_risk() -> pd.DataFrame:
    df, _, _ = assess_all(load_key(), load_emails(), load_register())
    return df


def evaluate(provider: str) -> dict:
    emails = {e.email_id: e for e in load_emails()}
    pred_path = ROOT / "outputs" / provider / "extractions.json"
    if not pred_path.exists():
        sys.exit(f"No results for '{provider}' yet. Run first: python -m leadtime_guard.run --provider {provider}")
    pred = {x["email_id"]: x for x in json.loads(pred_path.read_text(encoding="utf-8"))}
    key = load_key()

    # ---- extraction: field by field ----
    rows = []
    for k in key:
        p = pred.get(k["email_id"], {})
        e = emails[k["email_id"]]
        kd, pd_ = parse_date_text(k["promised_date_text"], e.date), parse_date_text(p.get("promised_date_text"), e.date)
        rows.append({
            "email_id": k["email_id"],
            "po_number": (p.get("po_number") or "").upper() == (k["po_number"] or "").upper(),
            "date": (kd.value, kd.ambiguous) == (pd_.value, pd_.ambiguous),
            "date_basis": p.get("date_basis") == k["date_basis"],
            "no_date_alert": (bool(p.get("delay_notice") or p.get("force_majeure") or p.get("fat_failed"))
                              and pd_.value is None and not pd_.ambiguous) ==
                             ((k["delay_notice"] or k["force_majeure"] or k["fat_failed"])
                              and kd.value is None and not kd.ambiguous),
            "evidence_found": bool(p.get("grounded")),
            "expected_date_text": k["promised_date_text"], "extracted_date_text": p.get("promised_date_text"),
        })
    ex = pd.DataFrame(rows)
    fields = ["po_number", "date", "date_basis", "no_date_alert", "evidence_found"]
    field_acc = pd.DataFrame([{"field": f, "accuracy_%": round(ex[f].mean() * 100, 1)} for f in fields])

    # ---- risk colours: all 25 items ----
    exp = expected_risk()[["item_id", "rag", "reasons"]].rename(columns={"rag": "expected", "reasons": "expected_why"})
    got = pd.read_csv(ROOT / "outputs" / provider / "risk_register.csv", dtype=str)[["item_id", "rag", "reasons"]]
    cmp_ = exp.merge(got.rename(columns={"rag": "predicted", "reasons": "predicted_why"}), on="item_id")
    m = rag_metrics(cmp_.expected, cmp_.predicted)
    cmp_["result"] = cmp_.apply(lambda r: "ok" if r.expected == r.predicted else
                                ("MISSED RISK" if r.predicted == "GREEN" else "different colour"), axis=1)
    return {"provider": provider, "extraction": ex, "field_accuracy": field_acc, "rag": m, "items": cmp_}


def write_report(res: dict):
    out = ROOT / "evals" / "results"
    out.mkdir(parents=True, exist_ok=True)
    m = res["rag"]
    exact = (res["items"].result == "ok").mean() * 100
    lines = [f"# Evaluation - extractor: `{res['provider']}`", "",
             f"- Emails: {len(res['extraction'])}, items: {len(res['items'])}",
             f"- Risky items in the answer key (amber/red): {m['risky_items']}",
             f"- **Missed risks (risky item rated green): {m['missed_risks']} -> missed-risk rate "
             f"{m['missed_risk_rate_%']}%** (target: at most 1 in about 20)",
             f"- Red recall: {m['red_recall_%']}% | false-alarm rate on green items: {m['false_alarm_rate_%']}%",
             f"- Items with exactly the right colour: {exact:.0f}%", "", "## Extraction accuracy", "",
             res["field_accuracy"].to_markdown(index=False), "", "## Confusion matrix (rows = expected)", "",
             m["confusion_matrix"].to_markdown(), "", "## Items where the colour differs", ""]
    diff = res["items"][res["items"].result != "ok"]
    lines.append(diff[["item_id", "expected", "predicted", "result", "expected_why"]].to_markdown(index=False)
                 if len(diff) else "None - every item has the expected colour.")
    wrong = res["extraction"][~res["extraction"].date]
    lines += ["", "## Emails where the date was read wrongly", "",
              wrong[["email_id", "expected_date_text", "extracted_date_text"]].to_markdown(index=False)
              if len(wrong) else "None."]
    md = out / f"eval_{res['provider']}.md"
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pd.ExcelWriter(out / f"eval_{res['provider']}.xlsx") as w:
        res["field_accuracy"].to_excel(w, sheet_name="Field accuracy", index=False)
        res["items"].to_excel(w, sheet_name="Items", index=False)
        res["extraction"].to_excel(w, sheet_name="Emails", index=False)
    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=PROVIDERS, default="offline")
    res = evaluate(ap.parse_args().provider)
    md = write_report(res)
    print(md.read_text(encoding="utf-8"))
    print(f"Saved: {md.relative_to(ROOT)} (+ .xlsx)")


if __name__ == "__main__":
    main()
