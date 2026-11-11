"""Read the supplier emails from data/emails/*.txt (simple 'Header: value' lines, a blank line, then the body)."""

from dataclasses import dataclass
from datetime import date
from email.utils import parsedate_to_datetime
from pathlib import Path

from .config import ROOT


@dataclass
class Email:
    email_id: str
    sender: str
    date: date
    subject: str
    body: str

    def text_for_model(self) -> str:
        return f"From: {self.sender}\nDate: {self.date.isoformat()}\nSubject: {self.subject}\n\n{self.body}"


def load_emails(folder: Path = ROOT / "data/emails") -> list[Email]:
    out = []
    for path in sorted(folder.glob("*.txt")):
        head, _, body = path.read_text(encoding="utf-8").partition("\n\n")
        h = dict(line.split(": ", 1) for line in head.splitlines() if ": " in line)
        out.append(Email(path.stem, h.get("From", ""), parsedate_to_datetime(h["Date"]).date(), h.get("Subject", ""),
                         body.strip()))
    return out


def without_quoted_text(body: str) -> str:
    """Remove quoted earlier emails (lines starting with '>') and everything after 'On ... wrote:'."""
    keep = []
    for line in body.splitlines():
        if line.lstrip().startswith(">") or (line.strip().startswith("On ") and line.strip().endswith("wrote:")):
            break
        keep.append(line)
    return "\n".join(keep)
