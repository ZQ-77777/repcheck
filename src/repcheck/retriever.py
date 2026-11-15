"""M2 — Select the pages the model needs to see.

Input : list[Page], TableTarget, template fields
Output: Context (at most `max_pages` pages, each kept with its page number)

Selection: (1) the table pages are always included; (2) other pages are ranked by
keyword hits for the checklist fields plus mentions of the table's variable names.
"""
from __future__ import annotations

import re

from .checklist_templates import FieldSpec
from .schemas import Context, Page, TableTarget

DEFAULT_MAX_PAGES = 8
APPENDIX_BONUS = 5           # variable-definition appendices are almost always needed
APPENDIX_RE = re.compile(r"variable definitions?|definitions? of variables", re.IGNORECASE)
_STOP = {"TABLE", "NOTES", "NOTE", "THIS", "YES", "NO", "OLS", "SIC", "CRSP", "FE"}


def table_variables(pages: list[Page], target: TableTarget) -> set[str]:
    """Upper-case tokens on the table pages, e.g. COVERAGE, SIZE, LEV."""
    text = " ".join(p.text for p in pages if p.number in target.pages)
    return {t for t in re.findall(r"\b[A-Z][A-Z_]{2,}\b", text) if t not in _STOP}


def keyword_hits(pages: list[Page], fields: list[FieldSpec]) -> dict[str, list[int]]:
    hits: dict[str, list[int]] = {}
    for f in fields:
        hits[f.key] = [p.number for p in pages if any(k in p.text.lower() for k in f.keywords)]
    return hits


def build_context(pages: list[Page], target: TableTarget, fields: list[FieldSpec],
                  max_pages: int = DEFAULT_MAX_PAGES) -> Context:
    hits = keyword_hits(pages, fields)
    variables = table_variables(pages, target)

    scores: dict[int, int] = {}
    for p in pages:
        if p.number in target.pages:
            continue
        s = sum(p.number in v for v in hits.values())
        s += sum(1 for v in variables if re.search(rf"\b{re.escape(v)}\b", p.text))
        if APPENDIX_RE.search(p.text):
            s += APPENDIX_BONUS
        if s > 0:
            scores[p.number] = s

    chosen = list(target.pages)
    for num, _ in sorted(scores.items(), key=lambda kv: (-kv[1], kv[0])):
        if len(chosen) >= max_pages:
            break
        chosen.append(num)

    by_num = {p.number: p.text for p in pages}
    chunks = [(n, by_num[n]) for n in sorted(chosen)]
    return Context(target=target, chunks=chunks, keyword_hits=hits)
