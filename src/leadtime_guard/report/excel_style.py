"""Excel styling (reused from the AI Data Room project, extended with green/amber/red)."""

from openpyxl.styles import Font, PatternFill

HEADER = PatternFill("solid", fgColor="1A3A5C")
RAG_FILL = {
    "red": PatternFill("solid", fgColor="F8D7DA"),
    "amber": PatternFill("solid", fgColor="FFF3CD"),
    "green": PatternFill("solid", fgColor="D4EDDA"),
}


def style_workbook(wb, rag_column: str = "rag") -> None:
    """Navy bold header, sensible column widths, and RAG colours on any column named `rag_column`."""
    for ws in wb.worksheets:
        headers = [c.value for c in ws[1]]
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = HEADER
        for col in ws.columns:
            width = max(len(str(c.value)) if c.value is not None else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(width + 2, 10), 60)
        ws.freeze_panes = "B2"
        if rag_column in headers:
            idx = headers.index(rag_column)
            for row in ws.iter_rows(min_row=2):
                fill = RAG_FILL.get(str(row[idx].value).lower())
                if fill:
                    for c in row:
                        c.fill = fill
