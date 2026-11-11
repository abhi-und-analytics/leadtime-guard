"""Risk engine: green / amber / red with reasons, from FIXED rules in config/risk_rules.yaml.

Order: red rules first, then amber, otherwise green. Every reason is written out in plain words,
so a planner can see exactly why an item has its colour. The thresholds are project assumptions.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from .. import config


@dataclass
class ItemUpdate:
    """Everything we know about one item after reading (and normalising) its latest supplier email."""
    email_id: Optional[str] = None
    email_date: Optional[date] = None
    supplier_date: Optional[date] = None
    on_site: Optional[date] = None
    precision: Optional[str] = None
    ambiguous: bool = False
    date_text: Optional[str] = None
    date_status: str = "unknown"
    delay_notice: bool = False
    force_majeure: bool = False
    fat_failed: bool = False
    partial_shipment: bool = False
    grounded: bool = True
    evidence: str = ""


@dataclass
class Assessment:
    rag: str
    reasons: list = field(default_factory=list)
    forecast_on_site: Optional[date] = None
    float_wd: Optional[int] = None
    milestone_moves: bool = False
    action: str = "none"           # none | chaser | escalation | internal_note


def assess(reg: dict, upd: Optional[ItemUpdate], today: Optional[date] = None) -> Assessment:
    r = config.rules()
    today = today or config.as_of()
    ros = date.fromisoformat(reg["ros_date"])
    successor_float = int(reg["successor_float_wd"])
    red, amber = [], []

    # Which on-site date do we believe? The new email if it gives one, otherwise the register forecast.
    no_date_now = upd is not None and upd.on_site is None and not upd.ambiguous and \
        (upd.delay_notice or upd.force_majeure or upd.fat_failed)
    if upd is not None and upd.on_site is not None:
        forecast = upd.on_site
    elif no_date_now:
        forecast = None
    else:
        forecast = date.fromisoformat(reg["current_forecast_on_site"])
    last_update = upd.email_date if upd and upd.email_date else date.fromisoformat(reg["last_update_date"])
    status = upd.date_status if upd else reg["date_status"]
    precision = upd.precision if upd else "day"

    # ---------- red ----------
    if upd and upd.force_majeure and forecast is None:
        red.append("force majeure notice without a revised date")
    elif upd and upd.fat_failed and forecast is None:
        red.append("FAT failed or missed, no new date")
    elif no_date_now:
        red.append("delay notice without a revised date")
    fl = config.float_wd(forecast, ros) if forecast else None
    moves = fl is not None and fl < 0 and -fl > successor_float
    if moves:
        red.append(f"{_wd(-fl)} late, more than the successor float of {successor_float} "
                   f"-> milestone {reg['milestone_id']} moves")

    # ---------- amber ----------
    if upd and upd.ambiguous:
        amber.append(f"ambiguous date '{upd.date_text}' (dd/mm or mm/dd?) - a person must confirm")
    if upd and not upd.grounded:
        amber.append("evidence sentence not found in the email - a person must check")
    if fl is not None and not moves and fl < int(r["amber"]["float_below_wd"]):
        amber.append(f"{_wd(-fl)} late, absorbed by successor float" if fl < 0
                     else f"float only {_wd(fl)}")
    weeks_to_ros = (ros - today).days / 7
    vague = status in ("tentative", "conditional") or precision in ("quarter", "month_part")
    if vague and weeks_to_ros <= int(r["amber"]["vague_date_within_weeks_of_ros"]) and forecast is not None:
        what = {"quarter": "quarter-level", "month_part": "month-level"}.get(precision, status)
        amber.append(f"{what} date within {r['amber']['vague_date_within_weeks_of_ros']} weeks of ROS")
    stale_limit = int(r["amber"]["stale_update_days"][reg["criticality_class"]])
    age = (today - last_update).days
    if age > stale_limit:
        amber.append(f"no supplier update for {age} days (limit {stale_limit} for class {reg['criticality_class']})")

    if red:
        action = "internal_note" if upd and upd.force_majeure else "escalation"
        return Assessment("red", red + amber, forecast, fl, moves, action)
    if amber:
        return Assessment("amber", amber, forecast, fl, False, "chaser")
    return Assessment("green", [f"float {_wd(fl)}, no warning signs"], forecast, fl, False, "none")


def _wd(n: int) -> str:
    return f"{n} working day" + ("" if n == 1 else "s")
