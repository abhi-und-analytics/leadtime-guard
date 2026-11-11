"""Write the results: risk register CSV + Excel report (with green/amber/red colours) + draft emails."""

from datetime import datetime

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils.dataframe import dataframe_to_rows

from ..config import ROOT, as_of
from ..pipeline import out_dir
from .excel_style import style_workbook


def _sheet(wb, title, df):
    ws = wb.create_sheet(title)
    for row in dataframe_to_rows(df, index=False, header=True):
        ws.append(row)
    return ws


def write_outputs(provider: str, df: pd.DataFrame, extractions: list, drafts: list) -> dict:
    d = out_dir(provider)
    df.to_csv(d / "risk_register.csv", index=False)

    # drafts: one text file each + a list with status "pending" (a person approves later)
    for f in d.glob("drafts/*.txt"):
        f.unlink()
    for x in drafts:
        (d / "drafts" / f"{x['item_id']}_{x['kind']}.txt").write_text(
            f"To: {x['to']}\nSubject: {x['subject']}\nStatus: PENDING APPROVAL (not sent)\n\n{x['body']}\n"
            + (f"\n---\nInternal: {x['internal_note']}\n" if x.get("internal_note") else ""), encoding="utf-8")
    drafts_df = pd.DataFrame([{**{k: v for k, v in x.items() if k != "body"}, "status": "pending"} for x in drafts])
    drafts_df.to_csv(d / "drafts.csv", index=False)

    counts = df.rag.value_counts()
    summary = pd.DataFrame([
        {"metric": "As-of date", "value": as_of().isoformat()},
        {"metric": "Extractor", "value": provider},
        {"metric": "Items", "value": len(df)},
        {"metric": "Red", "value": int(counts.get("RED", 0))},
        {"metric": "Amber", "value": int(counts.get("AMBER", 0))},
        {"metric": "Green", "value": int(counts.get("GREEN", 0))},
        {"metric": "Draft emails waiting for approval", "value": len(drafts)},
        {"metric": "Generated", "value": datetime.now().strftime("%Y-%m-%d %H:%M")},
    ])
    wb = Workbook()
    wb.remove(wb.active)
    _sheet(wb, "Summary", summary)
    _sheet(wb, "Risk register", df.assign(rag=df.rag.str.lower()))
    _sheet(wb, "Extractions", pd.DataFrame(extractions))
    if len(drafts_df):
        _sheet(wb, "Drafts (pending)", drafts_df)
    style_workbook(wb, rag_column="rag")
    wb["Summary"].freeze_panes = None
    for c in wb["Summary"]["A"]:
        c.font = Font(bold=True, color="FFFFFF" if c.row == 1 else "000000")
    xlsx = d / "LeadTime_Guard_report.xlsx"
    wb.save(xlsx)
    return {"csv": d / "risk_register.csv", "xlsx": xlsx, "drafts": d / "drafts"}
