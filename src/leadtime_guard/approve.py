"""Human approval of draft emails. NOTHING is ever sent by LeadTime Guard - a person decides.

    python -m leadtime_guard.approve --provider offline            # go through pending drafts one by one
    python -m leadtime_guard.approve --provider offline --list     # only show them

Every decision is written to outputs/<provider>/approval_log.csv (who, when, what).
Approved drafts are copied to outputs/<provider>/approved/ to send from your normal mail program.
"""

import argparse
import getpass
import shutil
from datetime import datetime

import pandas as pd

from .config import ROOT
from .pipeline import PROVIDERS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=PROVIDERS, default="offline")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    d = ROOT / "outputs" / a.provider
    if not (d / "drafts.csv").exists():
        raise SystemExit(f"No drafts yet. Run: python -m leadtime_guard.run --provider {a.provider}")
    drafts = pd.read_csv(d / "drafts.csv", dtype=str).fillna("")
    log_path = d / "approval_log.csv"
    done = set(pd.read_csv(log_path, dtype=str).item_id) if log_path.exists() else set()
    pending = drafts[~drafts.item_id.isin(done)]
    print(f"{len(pending)} draft(s) waiting for a decision.\n")
    if a.list:
        print(pending[["item_id", "kind", "to", "subject"]].to_string(index=False))
        return
    (d / "approved").mkdir(exist_ok=True)
    log = []
    for r in pending.to_dict("records"):
        f = d / "drafts" / f"{r['item_id']}_{r['kind']}.txt"
        print("=" * 80 + "\n" + f.read_text(encoding="utf-8"))
        ans = input("[a]pprove  [r]eject  [s]kip  [q]uit > ").strip().lower()[:1]
        if ans == "q":
            break
        if ans not in ("a", "r"):
            continue
        decision = "approved" if ans == "a" else "rejected"
        if decision == "approved":
            shutil.copy(f, d / "approved" / f.name)
        log.append({"item_id": r["item_id"], "kind": r["kind"], "decision": decision,
                    "by": getpass.getuser(), "at": datetime.now().isoformat(timespec="seconds")})
        print(f"-> {decision}\n")
    if log:
        new = pd.DataFrame(log)
        new.to_csv(log_path, mode="a", header=not log_path.exists(), index=False)
        print(f"Logged {len(log)} decision(s) in {log_path.relative_to(ROOT)}. Nothing was sent automatically.")


if __name__ == "__main__":
    main()
