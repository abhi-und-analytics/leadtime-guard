"""Run the whole pipeline.

    python -m leadtime_guard.run                     # offline baseline, no AI needed (works everywhere)
    python -m leadtime_guard.run --provider opencode # AI extraction with the free OpenCode CLI
    python -m leadtime_guard.run --provider opencode --use-cache   # reuse the last AI answers (no new calls)

(Run from the project folder with the virtual environment active. `src` must be on the path:
 the README shows `set PYTHONPATH=src` on Windows.)
"""

import argparse

from .config import ROOT, as_of
from .pipeline import PROVIDERS, run


def main():
    ap = argparse.ArgumentParser(description="LeadTime Guard - delivery-risk check for long-lead equipment")
    ap.add_argument("--provider", choices=PROVIDERS, default="offline",
                    help="offline = rule-based baseline (no AI); others = free AI providers")
    ap.add_argument("--use-cache", action="store_true", help="reuse saved extractions instead of new AI calls")
    args = ap.parse_args()
    print(f"LeadTime Guard | FRA-DC1 (fictional) | as of {as_of()} | extractor: {args.provider}")
    df, drafts, unmatched, paths = run(args.provider, args.use_cache)
    c = df.rag.value_counts()
    print(f"\nResult: {c.get('RED', 0)} red, {c.get('AMBER', 0)} amber, {c.get('GREEN', 0)} green "
          f"({len(df)} items)\n")
    show = df[df.rag != "GREEN"][["item_id", "rag", "on_site_forecast", "ros_date", "float_wd", "reasons"]]
    with __import__("pandas").option_context("display.width", 200, "display.max_colwidth", 70):
        print(show.to_string(index=False))
    if unmatched:
        print(f"\nEmails without a known PO number (check by hand): {', '.join(unmatched)}")
    print(f"\n{len(drafts)} draft email(s) waiting for approval (nothing was sent).")
    for k, p in paths.items():
        print(f"  {k:7}: {p.relative_to(ROOT)}")
    print("\nNext: python -m leadtime_guard.approve --provider", args.provider)


if __name__ == "__main__":
    main()
