"""Writes data/answer_key/expected_risk.csv: the expected colour of all 25 items, from the TRUE facts in
extraction_key.csv run through the same fixed rules. Review this file by hand - it is the yardstick.
Run: python scripts/build_expected_risk.py"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from leadtime_guard.evaluate import expected_risk  # noqa: E402

df = expected_risk()
df[["item_id", "description", "email_id", "supplier_says", "date_basis", "on_site_forecast", "ros_date", "float_wd",
    "rag", "reasons"]].to_csv(ROOT / "data/answer_key/expected_risk.csv", index=False)
print(df.rag.value_counts().to_string())
