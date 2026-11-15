"""M1 — PDF parsing.

Input : path to a PDF file
Output: list[Page] with cleaned text and 1-based page numbers
Errors: InvalidPDFError (cannot be opened), ScannedPDFError (no text layer)
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pdfplumber

from .schemas import Page
from .text_utils import clean_text

# A text PDF has hundreds of characters per page; a scanned one has almost none.
MIN_CHARS_PER_PAGE = 200


class InvalidPDFError(Exception):
    """The file is not a readable PDF."""


class ScannedPDFError(Exception):
    """The PDF has no usable text layer (e.g. a scan). OCR is out of scope."""


# Journals such as RFS typeset tables and notes so tightly that word gaps fall below pdfplumber's
# default tolerance and words run together ("Thedependentvariableis..."). Lines with such run-on
# tokens are re-extracted with a tolerance relative to the font size.
LONG_TOKEN = 18
TIGHT_TOLERANCE_RATIO = 0.15


def _longest_token(line: str) -> int:
    return max((len(t) for t in line.split()), default=0)


def _page_text(page) -> str:
    text = page.extract_text() or ""
    if not any(_longest_token(ln) >= LONG_TOKEN for ln in text.splitlines()):
        return text
    try:
        tight = page.extract_text(x_tolerance_ratio=TIGHT_TOLERANCE_RATIO) or ""
    except TypeError:  # pdfplumber older than 0.11
        tight = page.extract_text(x_tolerance=1.5) or ""
    default_lines, tight_lines = text.splitlines(), tight.splitlines()
    if len(default_lines) != len(tight_lines):
        return tight if len(tight.split()) > 1.3 * len(text.split()) else text
    return "\n".join(t if _longest_token(d) >= LONG_TOKEN and _longest_token(t) < _longest_token(d) else d
                     for d, t in zip(default_lines, tight_lines))


def parse_pdf(path: str | Path) -> list[Page]:
    try:
        with pdfplumber.open(str(path)) as pdf:
            pages = [Page(i, clean_text(_page_text(p))) for i, p in enumerate(pdf.pages, 1)]
    except Exception as exc:  # pdfminer raises several unrelated exception types
        raise InvalidPDFError(f"Cannot read '{Path(path).name}' as a PDF: {exc}") from exc
    if not pages:
        raise InvalidPDFError(f"'{Path(path).name}' has no pages.")
    total = sum(len(p.text.strip()) for p in pages)
    if total < MIN_CHARS_PER_PAGE * len(pages):
        raise ScannedPDFError(
            f"'{Path(path).name}' has almost no extractable text ({total} characters in "
            f"{len(pages)} pages). It looks like a scanned PDF; please use a text-based PDF."
        )
    return pages


def file_hash(path: str | Path) -> str:
    """SHA-256 of the PDF bytes; identifies a paper for caching (stable across machines)."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def guess_title(pages: list[Page]) -> str | None:
    """First title-cased line near the top of page 1 (display only)."""
    small = {"a", "an", "and", "the", "of", "in", "on", "for", "to", "with", "or", "at", "by", "from"}
    for line in pages[0].text.splitlines()[:10]:
        words = [w for w in line.split() if w.lower() not in small]
        if 15 <= len(line) <= 150 and words and \
                sum(w[0].isupper() for w in words) / len(words) >= 0.8 and not line.isupper():
            return line
    return None
