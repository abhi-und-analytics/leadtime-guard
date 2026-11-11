"""Day 1 check: is the equipment register and milestone list consistent?

Run:   python scripts/check_register.py
It prints errors (must fix) and warnings (look at them), shows today's float per item,
and writes data/register/equipment_register.xlsx (German Excel opens .csv files badly, the .xlsx always works).
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from leadtime_guard.report.excel_style import style_workbook  # noqa: E402

CFG = yaml.safe_load((ROOT / "config/project.yaml").read_text(encoding="utf-8"))
RULES = yaml.safe_load((ROOT / "config/risk_rules.yaml").read_text(encoding="utf-8"))
AS_OF = date.fromisoformat(str(CFG["project"]["as_of_date"]))
HOLIDAYS = [np.datetime64(str(d)) for d in CFG["holidays"]]

# Reference PO-to-ex-works lead times in weeks (sourced ranges; busway/CRAH/BMS etc. are assumptions)
LEAD_RANGES = {"transformer": (75, 130), "mv_switchgear": (52, 104), "lv_switchboard": (40, 85),
               "generator": (70, 110), "ups": (30, 48), "chiller": (30, 60)}

REQUIRED = ["item_id", "description", "category", "hall", "criticality_class", "supplier", "po_number", "po_date",
            "incoterm", "origin_region", "supplier_date_basis", "baseline_on_site", "current_forecast_on_site",
            "date_status", "ros_date", "milestone_id", "successor_float_wd", "last_update_date"]


def easter(year: int) -> date:
    """Anonymous Gregorian algorithm, used to double-check the Easter-based holidays in the config."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month = (h + l_ - 7 * m + 114) // 31
    day = ((h + l_ - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def wd_between(a: date, b: date) -> int:
    """Working days from a to b (negative if b is before a). Holidays from config."""
    return int(np.busday_count(np.datetime64(a), np.datetime64(b), holidays=HOLIDAYS))


def main():
    errors, warnings = [], []
    reg = pd.read_csv(ROOT / "data/register/equipment_register.csv", dtype=str)
    ms = pd.read_csv(ROOT / "data/register/milestones.csv", dtype=str)

    # 1. holidays: Easter-based dates present?
    hol = {str(d) for d in CFG["holidays"]}
    for y in (2026, 2027):
        e = easter(y)
        for name, off in [("Good Friday", -2), ("Easter Monday", 1), ("Ascension", 39), ("Whit Monday", 50),
                          ("Corpus Christi", 60)]:
            if str(e + timedelta(days=off)) not in hol:
                errors.append(f"Holiday missing in config: {name} {y} = {e + timedelta(days=off)}")

    # 2. columns and unique ids
    missing = [c for c in REQUIRED if c not in reg.columns]
    if missing:
        errors.append(f"Missing columns: {missing}")
    if reg["item_id"].duplicated().any():
        errors.append("Duplicate item_id values")
    if reg["po_number"].duplicated().any():
        errors.append("Duplicate po_number values")

    ms_dates = {r.milestone_id: date.fromisoformat(r.planned_date) for r in ms.itertuples()}
    rows = []
    for r in reg.itertuples():
        po, base, fc, ros = (date.fromisoformat(x) for x in (r.po_date, r.baseline_on_site,
                                                               r.current_forecast_on_site, r.ros_date))
        upd = date.fromisoformat(r.last_update_date)
        if po > AS_OF:
            errors.append(f"{r.item_id}: PO date {po} is after the as-of date {AS_OF}")
        if upd > AS_OF:
            errors.append(f"{r.item_id}: last update {upd} is after the as-of date")
        if r.milestone_id not in ms_dates:
            errors.append(f"{r.item_id}: unknown milestone {r.milestone_id}")
        elif ros >= ms_dates[r.milestone_id]:
            errors.append(f"{r.item_id}: ROS {ros} is not before milestone {r.milestone_id} {ms_dates[r.milestone_id]}")
        if base > ros:
            warnings.append(f"{r.item_id}: baseline on-site {base} is already after ROS {ros}")
        if isinstance(r.fat_planned, str) and r.fat_planned and date.fromisoformat(r.fat_planned) > date.fromisoformat(r.baseline_supplier_date):
            errors.append(f"{r.item_id}: FAT is after the supplier ship date (FAT is the ship gate)")
        if r.category in LEAD_RANGES:
            lo, hi = LEAD_RANGES[r.category]
            if not lo <= int(r.lead_time_weeks) <= hi:
                warnings.append(f"{r.item_id}: lead time {r.lead_time_weeks} wk outside reference range {lo}-{hi}")
        float_wd = wd_between(fc, ros)
        stale_limit = RULES["amber"]["stale_update_days"][r.criticality_class]
        age = (AS_OF - upd).days
        if age > stale_limit:
            warnings.append(f"{r.item_id}: last update {age} days old (> {stale_limit} for class {r.criticality_class})"
                            " - good: the risk engine should flag this as stale")
        rows.append({"item_id": r.item_id, "category": r.category, "forecast_on_site": fc, "ros_date": ros,
                     "float_wd_today": float_wd, "date_status": r.date_status, "update_age_days": age})

    # 3. milestone predecessors exist
    known = set(reg["item_id"]) | set(ms["milestone_id"])
    for r in ms.itertuples():
        for p in str(r.predecessors).split(";"):
            if p and p not in known:
                errors.append(f"Milestone {r.milestone_id}: unknown predecessor {p}")

    view = pd.DataFrame(rows)
    print(f"Register: {len(reg)} items, {len(ms)} milestones, as-of date {AS_OF}\n")
    print(view.to_string(index=False))
    print(f"\nLowest float: {view.float_wd_today.min()} working days; items under 20 wd: "
          f"{(view.float_wd_today < RULES['amber']['float_below_wd']).sum()}")

    out = ROOT / "data/register/equipment_register.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        reg.to_excel(xw, sheet_name="Register", index=False)
        ms.to_excel(xw, sheet_name="Milestones", index=False)
        view.to_excel(xw, sheet_name="Float today", index=False)
        style_workbook(xw.book)
    print(f"\nExcel copy written: {out.relative_to(ROOT)}")

    for w in warnings:
        print("WARNING:", w)
    for e in errors:
        print("ERROR:", e)
    print("\nRESULT:", "PASS" if not errors else f"FAIL ({len(errors)} errors)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
