"""Explain why one table is (or is not) found in a PDF.

  python scripts/diagnose_table.py examples/private/jw2020.pdf --table 4

`cli.py tables` only says whether a caption was accepted. This script shows what the parser saw
on every candidate page, which is what you need when a table that is visibly there is missing:

  * every line that looks like a caption for that number, with its score and why it was rejected;
  * pages whose running text mentions the table but where no caption line starts;
  * the page orientation (the /Rotate attribute and the share of sideways characters), because
    journals print wide tables sideways and pdfplumber then returns one word per line.

Exit code 0 if the table is located, 1 if not, so it can be used in a script.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from repcheck.pdf_parser import parse_pdf                       # noqa: E402
from repcheck.table_locator import (CAPTION_RE, TableNotFoundError, find_candidates,  # noqa: E402
                                    locate_table, pages_mentioning, parse_label, roman_to_int)


def _orientation(path: Path) -> dict[int, tuple[float, float]]:
    """page number -> (/Rotate angle, share of characters that are not upright)."""
    out = {}
    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            chars = [c for c in page.chars if c["text"]]
            share = sum(not c.get("upright", True) for c in chars) / len(chars) if chars else 0.0
            out[i] = (page.rotation, share)
    return out


def _caption_lines(pages, number: int):
    """All caption-looking lines for `number`, including the ones scoring 0 or less."""
    scored = {(c.page, c.line_idx): c for c in find_candidates(pages) if c.number == number}
    rows = []
    for page in pages:
        for idx, line in enumerate(page.text.splitlines()):
            m = CAPTION_RE.match(line)
            if not m:
                continue
            tok = m.group(1)
            try:
                n = int(tok) if tok.isdigit() else roman_to_int(tok)
            except KeyError:
                continue
            if n != number:
                continue
            cand = scored.get((page.number, idx))
            rows.append((page.number, line.strip(), cand.score if cand else None))
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--table", required=True, help="table label, e.g. 4, 'Table 4' or 'IV'")
    args = ap.parse_args(argv)

    path = Path(args.pdf)
    number = parse_label(args.table)
    pages = parse_pdf(path)
    orientation = _orientation(path)

    print(f"{path.name}: {len(pages)} pages")
    rotated = [f"p.{n} (rotate {rot:.0f}, {share:.0%} sideways)"
               for n, (rot, share) in orientation.items() if rot or share >= 0.05]
    print(f"Rotated pages: {', '.join(rotated) if rotated else 'none'}")

    lines = _caption_lines(pages, number)
    print(f"\nCaption-like lines for Table {number}: {len(lines) or 'none'}")
    for page, line, score in lines:
        verdict = "accepted" if score is not None and score > 0 else "rejected (score not positive)"
        print(f"  p.{page:<4} score={score}  {verdict}\n         {line[:110]!r}")

    mentions = pages_mentioning(pages, number)
    if mentions:
        print(f"\nProse mentions of Table {number}: page(s) {', '.join(map(str, mentions))}")
        for n in mentions:
            rot, share = orientation[n]
            print(f"  p.{n}: /Rotate={rot:.0f}, sideways characters {share:.0%}")

    try:
        target = locate_table(pages, args.table)
    except TableNotFoundError as exc:
        print(f"\nRESULT: not found — {exc}")
        if mentions and not any(rot or share > 0.3 for n in mentions for rot, share in [orientation[n]]):
            print("Hint: the pages that mention the table carry no caption text at all, which is what a")
            print("      caption rendered as an image looks like. OCR is out of scope; add the caption")
            print("      as text or treat the paper as unsupported (see docs/PARSER_NOTES.md).")
        return 1

    print(f"\nRESULT: found on page(s) {target.pages}")
    print(f"  caption: {target.caption[:110]!r}")
    print(f"  notes:   {target.notes[:110]!r}")
    for n in target.pages:
        rot, share = orientation[n]
        print(f"  p.{n}: /Rotate={rot:.0f}, sideways characters {share:.0%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
