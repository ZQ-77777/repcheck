"""M7 (stage 2) — Build a PaperTable from the model's transcription and verify every number.

A number is accepted only if the exact printed string occurs on the table page(s).
Numbers are easier to verify than prose: a misread digit is caught, not hidden.
"""
from __future__ import annotations

import re

from .schemas import Page, PaperTable, TableCell, TableColumn, TableTarget
from .text_utils import number_in_text, numeric_core


def to_float(raw) -> float | None:
    core = numeric_core(str(raw)) if raw not in (None, "") else None
    return float(core.replace(",", "")) if core else None


def to_int(raw) -> int | None:
    f = to_float(raw)
    return int(round(f)) if f is not None else None


def normalize_column_label(label) -> str:
    m = re.search(r"\d+", str(label))
    return f"({m.group(0)})" if m else str(label).strip()


def build_paper_table(raw: dict, target: TableTarget, pages: list[Page], model_name: str) -> PaperTable:
    text = "\n".join(p.text for p in pages if p.number in target.pages)
    columns = []
    for col in raw.get("columns", []):
        cells = []
        for row in col.get("rows", []):
            coef_raw = str(row.get("coef") or "").strip()
            paren_raw = str(row.get("paren") or "").strip() or None
            if not coef_raw or not row.get("variable"):
                continue
            ok = number_in_text(coef_raw, text) and (paren_raw is None or number_in_text(paren_raw, text))
            cells.append(TableCell(variable=str(row["variable"]).strip(), coef_raw=coef_raw,
                                   paren_raw=paren_raw, coef=to_float(coef_raw), paren=to_float(paren_raw),
                                   stars=min(3, coef_raw.count("*")), verified=ok))
        n_raw = str(col.get("n")).strip() if col.get("n") not in (None, "") else None
        kind = str(col.get("paren_kind") or "se").lower()
        columns.append(TableColumn(
            label=normalize_column_label(col.get("label", f"({len(columns) + 1})")),
            dependent_var=col.get("dependent_var"),
            paren_kind=kind if kind in ("se", "t", "none") else "se",
            n_raw=n_raw, n=to_int(n_raw), n_verified=bool(n_raw) and number_in_text(n_raw, text),
            cells=cells))
    return PaperTable(label=target.label, model_name=model_name, columns=columns)
