"""M1 — Locate the table the user asked for.

Input : list[Page], a label such as "Table 3", "3", "III" or "table iii"
Output: TableTarget (pages, caption, notes)
Errors: TableNotFoundError (lists the tables that were found)

Why scoring is needed: prose such as "Table 3 reports ..." also starts lines, but
only the caption sits on a page full of numbers, usually with "This table ..." notes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .schemas import Page, TableTarget

_ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
# Tolerant spelling: PDF text often loses or adds spaces ("Table3", "T able 3", "T A B L E 3").
CAPTION_RE = re.compile(r"^\s*t\s?a\s?b\s?l\s?e\s*([0-9]+|[ivxlc]+)\b\s*[.:\-]?\s*(.*)$", re.IGNORECASE)
NOTES_RE = re.compile(r"^\s*(notes?\b|this table\b)", re.IGNORECASE)
MENTION_RE = re.compile(r"\btable\s*(?:no\.?\s*)?([0-9]+|[ivxlc]+)\b", re.IGNORECASE)

# Scoring weights (kept as constants so a teammate can tune them without reading the logic)
W_TITLE_LIKE = 1        # caption text after the label looks like a title
W_PROSE_LIKE = -3       # "Table 3 reports ..." -> prose, not a caption
W_NUMERIC_PAGE = 1      # page is dense with digits
W_TABLE_NOTES = 2       # page contains "This table ..." / "Notes:"
NUMERIC_DENSITY = 0.12  # share of digit characters that counts as "dense"


class TableNotFoundError(Exception):
    def __init__(self, label: str, available: list[str], mentions: list[int] | None = None):
        self.label, self.available = label, available
        self.mentions = mentions or []
        found = ", ".join(available) if available else "none"
        message = f"Could not find '{label}' in the PDF. Tables found: {found}."
        if self.mentions:
            pages = ", ".join(str(n) for n in self.mentions)
            message += (f" The running text mentions '{label}' on page(s) {pages}, but no caption line"
                        " starts there: the caption may be set as an image, or the table may be printed"
                        " sideways. Try `python scripts/diagnose_table.py PAPER.pdf --table"
                        f" {label.split()[-1]}` to see what the page contains.")
        super().__init__(message)


@dataclass
class _Candidate:
    page: int
    line_idx: int
    number: int
    rest: str
    continued: bool
    score: int


def roman_to_int(s: str) -> int:
    s, total, prev = s.upper(), 0, 0
    for ch in reversed(s):
        v = _ROMAN[ch]
        total = total - v if v < prev else total + v
        prev = max(prev, v)
    return total


def parse_label(label: str) -> int:
    m = re.fullmatch(r"\s*(?:table\s+)?([0-9]+|[ivxlc]+)\s*", label, re.IGNORECASE)
    if not m:
        raise ValueError(f"Cannot understand table label '{label}'. Use e.g. 'Table 3' or 'III'.")
    tok = m.group(1)
    return int(tok) if tok.isdigit() else roman_to_int(tok)


def _numeric_density(text: str) -> float:
    chars = [c for c in text if not c.isspace()]
    return sum(c.isdigit() for c in chars) / max(1, len(chars))


def _score(rest: str, page_text: str) -> int:
    score = 0
    words = rest.split()
    if not rest or rest[0] in "(:" or rest[0].isupper():
        score += W_TITLE_LIKE
    if words and words[0][0].islower():
        score += W_PROSE_LIKE
    if _numeric_density(page_text) >= NUMERIC_DENSITY:
        score += W_NUMERIC_PAGE
    if any(NOTES_RE.match(ln) for ln in page_text.splitlines()):
        score += W_TABLE_NOTES
    return score


def find_candidates(pages: list[Page]) -> list[_Candidate]:
    out = []
    for p in pages:
        for idx, line in enumerate(p.text.splitlines()):
            m = CAPTION_RE.match(line)
            if not m:
                continue
            tok, rest = m.group(1), m.group(2).strip()
            try:
                number = int(tok) if tok.isdigit() else roman_to_int(tok)
            except KeyError:
                continue
            continued = "continued" in rest.lower()
            out.append(_Candidate(p.number, idx, number, rest, continued, _score(rest, p.text)))
    return out


def list_tables(pages: list[Page]) -> list[str]:
    nums = sorted({c.number for c in find_candidates(pages) if c.score > 0 and not c.continued})
    return [f"Table {n}" for n in nums]


def pages_mentioning(pages: list[Page], number: int) -> list[int]:
    """Pages whose running text refers to "Table N" (diagnostics for a missing caption)."""
    out: list[int] = []
    for p in pages:
        for m in MENTION_RE.finditer(p.text):
            tok = m.group(1)
            try:
                n = int(tok) if tok.isdigit() else roman_to_int(tok)
            except KeyError:
                continue
            if n == number:
                out.append(p.number)
                break
    return out


def _extract_notes(text: str) -> str:
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if NOTES_RE.match(ln):
            return " ".join(lines[i:]).strip()
    return ""


def locate_table(pages: list[Page], label: str) -> TableTarget:
    number = parse_label(label)
    canonical = f"Table {number}"
    cands = [c for c in find_candidates(pages) if c.number == number and c.score > 0]
    main = [c for c in cands if not c.continued]
    if not main:
        raise TableNotFoundError(canonical, list_tables(pages), pages_mentioning(pages, number))
    best = max(main, key=lambda c: (c.score, -c.page))

    by_num = {p.number: p for p in pages}
    table_pages = [best.page]
    nxt = best.page + 1
    while any(c.page == nxt and c.continued for c in cands):
        table_pages.append(nxt)
        nxt += 1

    lines = by_num[best.page].text.splitlines()
    caption = lines[best.line_idx]
    if not best.rest and best.line_idx + 1 < len(lines):
        caption = f"{caption} {lines[best.line_idx + 1]}"
    notes = " ".join(n for n in (_extract_notes(by_num[p].text) for p in table_pages) if n)
    return TableTarget(label=canonical, number=number, pages=table_pages, caption=caption, notes=notes)
