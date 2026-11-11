"""The whole pipeline in one place: read emails -> extract -> check evidence -> normalise dates ->
rate risk -> draft emails -> report. Used by run.py, evaluate.py, the tests and the dashboard."""

import json
import os
from datetime import date
from pathlib import Path

import pandas as pd

from .actions.drafts import make_draft
from .config import ROOT
from .emails import Email, load_emails
from .extract.grounding import is_grounded
from .normalise.dates import parse_date_text, to_on_site
from .rules.engine import ItemUpdate, assess
from .schema import SupplierUpdate

PROVIDERS = ["offline", "opencode", "gemini", "ollama", "groq"]


def load_register() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data/register/equipment_register.csv", dtype=str).fillna("")


def out_dir(provider: str) -> Path:
    d = ROOT / "outputs" / provider
    (d / "drafts").mkdir(parents=True, exist_ok=True)
    return d


# ---------- step 1-2: extraction (+ evidence check) ----------
def extract_all(provider: str, emails: list[Email], use_cache: bool = False, log=print) -> list[dict]:
    cache = out_dir(provider) / "extractions.json"
    if use_cache and cache.exists():
        log(f"Using cached extractions: {cache.relative_to(ROOT)}")
        return json.loads(cache.read_text(encoding="utf-8"))
    if provider == "offline":
        from .extract.baseline import extract as baseline_extract
        rows = []
        for e in emails:
            u = baseline_extract(e)
            rows.append({"email_id": e.email_id, **u.model_dump(), "grounded": is_grounded(u.evidence_quote, e.body)})
    else:
        os.environ["LTG_PROVIDER"] = provider
        from .extract.llm_extractor import LLMExtractor
        ex = LLMExtractor()
        # Resume: emails that already worked in an earlier (interrupted) run are reused, not sent again.
        done = {}
        if cache.exists():
            done = {r["email_id"]: r for r in json.loads(cache.read_text(encoding="utf-8"))
                    if not str(r.get("evidence_quote", "")).startswith("EXTRACTION FAILED")}
        rows = []
        for i, e in enumerate(emails, 1):
            if e.email_id in done:
                rows.append(done[e.email_id])
                log(f"  [{i}/{len(emails)}] {e.email_id} ... done earlier (reused)") if log is print else None
                continue
            log(f"  [{i}/{len(emails)}] {e.email_id} ...", end=" ", flush=True) if log is print else None
            try:
                u, grounded = ex.extract(e)
                rows.append({"email_id": e.email_id, **u.model_dump(), "grounded": grounded})
                cache.write_text(json.dumps(rows + [r for k, r in done.items() if k not in {x["email_id"] for x in rows}],
                                            indent=2, ensure_ascii=False), encoding="utf-8")   # save progress
                log("ok" if grounded else "evidence NOT found -> flagged") if log is print else None
            except Exception as err:   # one bad answer must not stop the run: flag it for a person
                log(f"failed ({str(err)[:80]}) -> flagged") if log is print else None
                if i == 3 and not done and all(r["evidence_quote"].startswith("EXTRACTION FAILED") for r in rows):
                    raise SystemExit(f"\nThe first 3 AI calls failed: {err}\nCheck the provider setup (README, step 4) "
                                     "or run without AI: python -m leadtime_guard.run --provider offline")
                rows.append({"email_id": e.email_id, "po_number": None, "promised_date_text": None,
                             "date_basis": "unknown", "date_status": "unknown", "delay_notice": False,
                             "force_majeure": False, "fat_failed": False, "partial_shipment": False,
                             "evidence_quote": f"EXTRACTION FAILED: {str(err)[:200]}", "grounded": False})
        log(ex.usage.summary())
    cache.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    return rows


# ---------- step 3: normalise one extraction ----------
def to_item_update(x: dict, email: Email, origin_region: str) -> ItemUpdate:
    p = parse_date_text(x.get("promised_date_text"), email.date)
    basis = x.get("date_basis") or "unknown"
    return ItemUpdate(email_id=x["email_id"], email_date=email.date, supplier_date=p.value,
                      on_site=to_on_site(p.value, basis, origin_region), precision=p.precision, ambiguous=p.ambiguous,
                      date_text=x.get("promised_date_text"), date_status=x.get("date_status") or "unknown",
                      delay_notice=bool(x.get("delay_notice")), force_majeure=bool(x.get("force_majeure")),
                      fat_failed=bool(x.get("fat_failed")), partial_shipment=bool(x.get("partial_shipment")),
                      grounded=bool(x.get("grounded", True)), evidence=x.get("evidence_quote") or "")


# ---------- steps 3-5 for all items ----------
def assess_all(extractions: list[dict], emails: list[Email], register: pd.DataFrame, today: date = None):
    by_id = {e.email_id: e for e in emails}
    po_to_item = dict(zip(register.po_number, register.item_id))
    latest = {}                                     # item_id -> (email date, extraction) - newest email wins
    unmatched = []
    for x in extractions:
        e = by_id[x["email_id"]]
        item = po_to_item.get((x.get("po_number") or "").strip().upper())
        if item is None:
            unmatched.append(x["email_id"])
            continue
        if item not in latest or e.date >= latest[item][0]:
            latest[item] = (e.date, x)
    rows, drafts = [], []
    for reg in register.to_dict("records"):
        x = latest.get(reg["item_id"], (None, None))[1]
        upd = to_item_update(x, by_id[x["email_id"]], reg["origin_region"]) if x else None
        a = assess(reg, upd, today)
        rows.append({
            "item_id": reg["item_id"], "description": reg["description"], "supplier": reg["supplier"],
            "po_number": reg["po_number"], "milestone": reg["milestone_id"], "class": reg["criticality_class"],
            "email_id": upd.email_id if upd else "", "supplier_says": (upd.date_text or "") if upd else "",
            "date_basis": (x.get("date_basis") if x else reg["supplier_date_basis"]),
            "on_site_forecast": a.forecast_on_site.isoformat() if a.forecast_on_site else "",
            "ros_date": reg["ros_date"], "float_wd": a.float_wd if a.float_wd is not None else "",
            "rag": a.rag.upper(), "reasons": "; ".join(a.reasons), "action": a.action,
            "evidence": upd.evidence if upd else "(no new email - register value used)",
        })
        d = make_draft(reg, a, upd)
        if d:
            drafts.append(d)
    order = {"RED": 0, "AMBER": 1, "GREEN": 2}
    df = pd.DataFrame(rows).sort_values(by=["rag", "item_id"], key=lambda s: s.map(order) if s.name == "rag" else s)
    return df.reset_index(drop=True), drafts, unmatched


def run(provider: str = "offline", use_cache: bool = False, log=print):
    emails = load_emails()
    register = load_register()
    extractions = extract_all(provider, emails, use_cache, log)
    df, drafts, unmatched = assess_all(extractions, emails, register)
    from .report.report import write_outputs
    paths = write_outputs(provider, df, extractions, drafts)
    return df, drafts, unmatched, paths


def update_from_dict(x: dict) -> SupplierUpdate:
    return SupplierUpdate(**{k: x.get(k) for k in SupplierUpdate.model_fields})
