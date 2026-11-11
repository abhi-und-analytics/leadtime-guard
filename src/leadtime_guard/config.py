"""Project configuration and working-day helpers (one place, used by every step)."""

from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]


@lru_cache
def project() -> dict:
    return yaml.safe_load((ROOT / "config/project.yaml").read_text(encoding="utf-8"))


@lru_cache
def rules() -> dict:
    return yaml.safe_load((ROOT / "config/risk_rules.yaml").read_text(encoding="utf-8"))


def as_of() -> date:
    return date.fromisoformat(str(project()["project"]["as_of_date"]))


def holidays():
    return [np.datetime64(str(d)) for d in project()["holidays"]]


def is_working_day(d: date) -> bool:
    return bool(np.is_busday(np.datetime64(d), holidays=holidays()))


def roll_forward(d: date) -> date:
    """Same day if it is a working day, otherwise the next working day."""
    return np.busday_offset(np.datetime64(d), 0, roll="forward", holidays=holidays()).astype(object)


def roll_backward(d: date) -> date:
    return np.busday_offset(np.datetime64(d), 0, roll="backward", holidays=holidays()).astype(object)


def add_working_days(d: date, n: int) -> date:
    """Roll to a working day first, then add n working days."""
    return np.busday_offset(np.datetime64(d), n, roll="forward", holidays=holidays()).astype(object)


def add_calendar_days(d: date, n: int) -> date:
    return d + timedelta(days=n)


def float_wd(on_site: date, ros: date) -> int:
    """Working days between the on-site date and the required-on-site (ROS) date.
    Positive = time to spare, negative = late."""
    if on_site <= ros:
        return int(np.busday_count(np.datetime64(on_site), np.datetime64(ros), holidays=holidays()))
    return -int(np.busday_count(np.datetime64(ros), np.datetime64(on_site), holidays=holidays()))
