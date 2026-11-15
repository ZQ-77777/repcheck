"""M4 — Turn the model's raw answer into a checked Checklist.

For every template field (not just the ones the model chose to answer):
  * no value                    -> MISSING, with a hint built from keyword hits (not by the model)
  * value, all quotes found     -> VERIFIED (a quote found on another page is page-corrected)
  * value, some quote not found -> UNVERIFIED, flagged for manual checking
"""
from __future__ import annotations

import re

from .checklist_templates import FieldSpec
from .schemas import Checklist, ChecklistItem, Context, Evidence, ExtractionStatus, Page
from .text_utils import partial_ratio

MATCH_THRESHOLD = 90.0   # partial-ratio score needed to accept a quote (tune on gold data)


def verify_evidence(ev: Evidence, pages: dict[int, str], threshold: float = MATCH_THRESHOLD) -> Evidence:
    if ev.page in pages and partial_ratio(ev.quote, pages[ev.page]) >= threshold:
        return Evidence(ev.page, ev.quote, verified=True)
    for num, text in pages.items():
        if num != ev.page and partial_ratio(ev.quote, text) >= threshold:
            return Evidence(num, ev.quote, verified=True, page_corrected=True)
    return Evidence(ev.page, ev.quote, verified=False)


def _clean_value(value, is_list: bool):
    if value in (None, "", []):
        return None
    if is_list:
        items = value if isinstance(value, list) else [value]
        items = [str(v).strip() for v in items if str(v).strip()]
        return items or None
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    return str(value).strip()


def _parse_evidence(raw) -> list[Evidence]:
    out = []
    for e in raw or []:
        try:
            page = re.search(r"\d+", str(e["page"]))   # accepts 4, "4", "p.4"
            out.append(Evidence(int(page.group()), str(e["quote"]).strip()))
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
    return [e for e in out if e.quote]


def missing_hint(spec: FieldSpec, context: Context) -> str:
    pages = context.keyword_hits.get(spec.key) or []
    if pages:
        listed = ", ".join(f"p.{p}" for p in pages[:6])
        return (f"Not found by the model. Keywords for this field appear on {listed}; "
                f"check them. If the paper does not report it, mark 'Not in paper'.")
    return (f"Not found, and no related keywords in the paper. Papers usually report this in "
            f"{spec.where}. It may be genuinely unreported: mark 'Not in paper' and note it.")


def build_item(spec: FieldSpec, raw_field: dict, pages: dict[int, str], context: Context) -> ChecklistItem:
    value = _clean_value(raw_field.get("value"), spec.is_list) if raw_field.get("found", True) else None
    if value is None:
        return ChecklistItem(spec.key, spec.label, spec.required, ExtractionStatus.MISSING,
                             hint=missing_hint(spec, context))
    evidence = [verify_evidence(e, pages) for e in _parse_evidence(raw_field.get("evidence"))]
    if not evidence:
        return ChecklistItem(spec.key, spec.label, spec.required, ExtractionStatus.UNVERIFIED, value,
                             hint="The model gave a value without a quote. Check it against the paper.")
    if all(e.verified for e in evidence):
        moved = [e for e in evidence if e.page_corrected]
        hint = (f"Page number corrected to {', '.join(f'p.{e.page}' for e in moved)}." if moved else None)
        return ChecklistItem(spec.key, spec.label, spec.required, ExtractionStatus.VERIFIED, value, evidence, hint)
    bad = [e for e in evidence if not e.verified]
    return ChecklistItem(
        spec.key, spec.label, spec.required, ExtractionStatus.UNVERIFIED, value, evidence,
        hint=f"{len(bad)} quote(s) could not be found in the PDF text — the value may be paraphrased "
             f"or invented. Check p.{bad[0].page} before confirming.")


def build_checklist(raw: dict, pages: list[Page], context: Context, fields: list[FieldSpec], *,
                    source_file: str, content_hash: str, template: str, model_name: str,
                    paper_title: str | None = None) -> Checklist:
    by_num = {p.number: p.text for p in pages}   # verify against the WHOLE paper, not just the context
    raw_fields = raw.get("fields", {}) if isinstance(raw, dict) else {}
    items = [build_item(f, raw_fields.get(f.key) or {"found": False}, by_num, context) for f in fields]
    return Checklist(source_file=source_file, content_hash=content_hash, table=context.target,
                     template=template, model_name=model_name, items=items, paper_title=paper_title)
