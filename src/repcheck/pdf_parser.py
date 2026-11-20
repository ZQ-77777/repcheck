"""M1 — PDF parsing.

Input : path to a PDF file
Output: list[Page] with cleaned text and 1-based page numbers
Errors: InvalidPDFError (cannot be opened), ScannedPDFError (no text layer)
"""
from __future__ import annotations

import hashlib
import math
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


# Journals print wide regression tables sideways: the page (or only the table block) is rotated 90°
# so that the reader turns the page. pdfplumber then returns one character or one word per line,
# often in reverse order ("4\nELBAT"), so no caption line survives. Pages where at least this share
# of the characters is not upright are re-flowed from the character boxes instead.
SIDEWAYS_SHARE = 0.30
SIDEWAYS_MIN_CHARS = 20
LINE_TOLERANCE = 3.0     # points between two baselines that still count as the same line


def _longest_token(line: str) -> int:
    return max((len(t) for t in line.split()), default=0)


def _sideways_chars(page) -> dict[float, list[dict]] | None:
    """Characters on a page whose text is rotated, grouped by the rotation to undo (degrees).

    A sideways table page usually carries text at more than one angle: the table and its caption
    at 90°, an upright publisher banner, and a download sidebar at 270°. Each group is re-flowed on
    its own axes and the largest group (the table) is emitted first.
    """
    chars = [c for c in page.chars if c["text"]]
    if len(chars) < SIDEWAYS_MIN_CHARS:
        return None
    sideways = [c for c in chars if not c.get("upright", True)]
    if len(sideways) / len(chars) < SIDEWAYS_SHARE:
        return None
    groups: dict[float, list[dict]] = {}
    for c in chars:
        angle = round(math.degrees(math.atan2(c["matrix"][1], c["matrix"][0])) / 90) * 90 % 360
        groups.setdefault(float(angle), []).append(c)
    return groups


def _reflow_rotated(text_chars: list[dict], angle: float) -> str:
    """Rebuild reading order from character boxes drawn along a rotated baseline.

    Every character is projected onto the text's own axes: `along` runs left to right inside a line,
    `across` separates the lines. Sorting by `across` (highest first) then `along` recovers the
    printed order for both 90° and 270° rotations, with or without a /Rotate page attribute.
    """
    theta = math.radians(angle)
    ca, sa = math.cos(theta), math.sin(theta)
    placed = []
    for c in text_chars:
        x, y = c["matrix"][4], c["matrix"][5]      # char origin in PDF coordinates (y up)
        along = x * ca + y * sa
        across = -x * sa + y * ca
        placed.append((across, along, c["text"]))
    placed.sort(key=lambda item: (round(item[0], 1), item[1]), reverse=True)
    # `reverse=True` also reverses `along`; restore left-to-right order inside each line.
    lines: list[list[tuple[float, str]]] = []
    line_keys: list[float] = []
    for across, along, ch in placed:
        if not lines or abs(across - line_keys[-1]) > LINE_TOLERANCE:
            lines.append([])
            line_keys.append(across)
        lines[-1].append((along, ch))
    return "\n".join("".join(ch for _, ch in sorted(line)) for line in lines)


def _page_text(page) -> str:
    groups = _sideways_chars(page)
    if groups is not None:
        # Largest block first: on a sideways table page that is the table and its caption; a
        # publisher banner or download sidebar is a small remainder appended after it.
        blocks = sorted(groups.items(), key=lambda item: -len(item[1]))
        return "\n".join(_reflow_rotated(chars, angle) for angle, chars in blocks)
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
