"""M8 (stage 2) — Compare a replication's results with the paper's table.

Input : PaperTable, list[ResultRow] (from a CSV), optional reviewed Checklist
Output: ComparisonReport; every discrepancy lists checklist items to re-check

Results CSV (long format, one row per coefficient):
    column,variable,coef,se,pvalue,n
    (1),COVERAGE,0.0121,0.0030,0.0001,24318
`se`, `pvalue` and `n` are optional. Column labels "1" and "(1)" are treated the same.

The diagnosis rules below are deliberately simple heuristics, written as data so the
team can extend them; they suggest where to look, they do not prove a cause.
"""
from __future__ import annotations

import csv
import io
from collections import Counter
from decimal import Decimal
from math import isfinite
from pathlib import Path

from .schemas import (Checklist, ComparisonReport, Discrepancy, PaperTable, ResultRow,
                      ReviewStatus)
from .table_numbers import normalize_column_label

REL_TOL = 0.05          # |replicated - paper| / |paper| above this is a magnitude difference
MAJOR_REL = 0.25        # above this the magnitude difference is "major"
N_TOL = 0.01            # relative difference in N tolerated
SCALE_FACTORS = (100.0, 1000.0)

SUSPECTS = {
    "n_mismatch": ["sample_filters", "subsamples", "sample_period", "data_sources"],
    "column_missing": ["model"],
    "variable_missing": ["controls", "key_independent_vars"],
    "sign_flip": ["dependent_var", "key_independent_vars", "controls"],
    "scale": ["dependent_var", "key_independent_vars", "controls"],
    "cross_column_scale": ["dependent_var", "key_independent_vars", "controls"],
    "magnitude": ["winsorization", "subsamples", "controls", "sample_filters", "fixed_effects"],
    "significance": ["standard_errors", "fixed_effects"],
    "se_mismatch": ["standard_errors"],
}


class ResultsFormatError(Exception):
    pass


def _opt_float(v):
    v = (v or "").strip()
    return float(v.replace(",", "")) if v and v.upper() not in ("NA", "NAN", ".") else None


def load_results_csv(source) -> list[ResultRow]:
    """`source`: path, or text / bytes of the CSV (as uploaded in the UI)."""
    if isinstance(source, (str, Path)) and Path(str(source)).exists():
        text = Path(source).read_text(encoding="utf-8-sig")
    elif isinstance(source, bytes):
        text = source.decode("utf-8-sig")
    else:
        text = str(source)
    reader = csv.DictReader(io.StringIO(text))
    fields = {f.strip().lower() for f in reader.fieldnames or []}
    missing = {"column", "variable", "coef"} - fields
    if missing:
        raise ResultsFormatError(f"Results CSV needs columns column, variable, coef; missing: {', '.join(sorted(missing))}.")
    rows = []
    for i, r in enumerate(reader, start=2):
        r = {k.strip().lower(): v for k, v in r.items() if k}
        try:
            n = _opt_float(r.get("n"))
            rows.append(ResultRow(column=normalize_column_label(r["column"]), variable=r["variable"].strip(),
                                  coef=float(r["coef"].replace(",", "")), se=_opt_float(r.get("se")),
                                  pvalue=_opt_float(r.get("pvalue")), n=int(n) if n is not None else None))
        except (ValueError, AttributeError) as exc:
            raise ResultsFormatError(f"Line {i} of the results CSV is not valid: {exc}") from exc
    if not rows:
        raise ResultsFormatError("The results CSV has no rows.")
    return rows


def stars_from(pvalue: float | None, t: float | None) -> int | None:
    if pvalue is None and t is None:
        return None
    if pvalue is not None:
        return 3 if pvalue < 0.01 else 2 if pvalue < 0.05 else 1 if pvalue < 0.10 else 0
    t = abs(t)
    return 3 if t >= 2.576 else 2 if t >= 1.960 else 1 if t >= 1.645 else 0


VARIABLE_FIELDS = {"dependent_var", "key_independent_vars", "controls"}


def _suspect_notes(keys: list[str], checklist: Checklist | None, variable: str | None = None) -> list[str]:
    """Readable pointers into the checklist. For variable-level problems, only that variable's
    definition is shown (other variables are irrelevant to the discrepancy)."""
    if checklist is None:
        return []
    notes = []
    for k in keys:
        item = checklist.get(k)
        if item is None:
            continue
        if item.review_status == ReviewStatus.NOT_IN_PAPER:
            notes.append(f"{item.label}: not reported in the paper — a likely source of differences.")
            continue
        value = item.final_value() or item.value
        if value is None:
            notes.append(f"{item.label}: not extracted — check the paper.")
            continue
        entries = value if isinstance(value, list) else [value]
        if variable and k in VARIABLE_FIELDS:
            entries = [e for e in entries if e.split(":")[0].strip().lower() == variable.lower()]
            if not entries:
                continue
        text = "; ".join(entries)
        text = text if len(text) <= 300 else text[:297].rsplit(" ", 1)[0] + " …"
        pages = sorted({e.page for e in item.evidence})
        where = f" (p.{', p.'.join(map(str, pages))})" if pages else ""
        notes.append(f"{item.label}: {text}{where}")
    if variable and not any(n.split(":")[0] in {"Dependent variable", "Key independent variable(s)",
                                                 "Control variables"} for n in notes) \
            and set(keys) & VARIABLE_FIELDS:
        notes.append(f"{variable}: no definition in the checklist — find it in the paper.")
    return notes


def _is_scaled(paper: float, rep: float) -> bool:
    if paper == 0 or rep == 0:
        return False
    ratio = abs(rep / paper)
    return any(abs(ratio / f - 1) < 0.1 or abs(ratio * f - 1) < 0.1 for f in SCALE_FACTORS)


def compare(paper: PaperTable, results: list[ResultRow], checklist: Checklist | None = None,
            rel_tol: float = REL_TOL, n_tol: float = N_TOL) -> ComparisonReport:
    out: list[Discrepancy] = []
    scale_samples = {}
    total = matched = 0

    def add(col, var, kind, severity, p, r, msg):
        keys = SUSPECTS[kind]
        out.append(Discrepancy(col, var, kind, severity, p, r, msg, keys, _suspect_notes(keys, checklist, var)))

    for col in paper.columns:
        rows = [r for r in results if r.column == col.label]
        if not rows:
            add(col.label, None, "column_missing", "major", col.label, None,
                f"Column {col.label} is not in the results file.")
            total += len(col.cells)
            continue
        rep_n = next((r.n for r in rows if r.n is not None), None)
        if col.n and rep_n and abs(rep_n - col.n) / col.n > n_tol:
            add(col.label, None, "n_mismatch", "major", f"{col.n:,}", f"{rep_n:,}",
                f"N differs by {100 * (rep_n - col.n) / col.n:+.1f}%; coefficient differences in this "
                f"column may follow from the sample difference.")
        by_var = {r.variable.lower(): r for r in rows}
        for cell in col.cells:
            if cell.coef is None:
                continue
            total += 1
            r = by_var.get(cell.variable.lower())
            if r is None:
                add(col.label, cell.variable, "variable_missing", "major", cell.coef_raw, None,
                    f"{cell.variable} is in the paper but not in the replication.")
                continue
            p, q = cell.coef, r.coef
            if cell.verified and p != 0 and isfinite(p) and isfinite(q):
                scale_samples.setdefault(cell.variable.lower(), {})[col.label] = (cell, q)
            ok = True
            if p != 0 and q != 0 and (p > 0) != (q > 0):
                add(col.label, cell.variable, "sign_flip", "major", cell.coef_raw, f"{q:.4g}",
                    "Opposite sign — check how the variable is defined or signed.")
                ok = False
            elif _is_scaled(p, q):
                add(col.label, cell.variable, "scale", "major", cell.coef_raw, f"{q:.4g}",
                    f"Off by a factor of about {abs(q / p):.3g} — likely a units/scaling difference "
                    "(e.g. percent vs. fraction).")
                ok = False
            elif p != 0 and abs(q - p) / abs(p) > rel_tol:
                rel = abs(q - p) / abs(p)
                add(col.label, cell.variable, "magnitude", "major" if rel > MAJOR_REL else "minor",
                    cell.coef_raw, f"{q:.4g}", f"Magnitude differs by {100 * rel:.0f}%.")
                ok = False
            elif (
                col.paren_kind == "se" and cell.verified
                and (p != 0 or q == 0)
                and cell.paren is not None and cell.paren > 0
                and r.se is not None and r.se >= 0
            ):
                paper_se = Decimal(str(cell.paren))
                se_gap = abs(Decimal(str(r.se)) - paper_se) / paper_se
                if se_gap > Decimal("0.25"):
                    add(col.label, cell.variable, "se_mismatch", "minor",
                        cell.paren_raw, f"{r.se:.4g}",
                        f"Standard errors differ by {se_gap:.1%}. Check the clustering level "
                        "and the standard-error estimator.")
            t = (q / r.se) if r.se else None
            rep_stars = stars_from(r.pvalue, t)
            if rep_stars is not None and rep_stars != cell.stars:
                add(col.label, cell.variable, "significance", "minor",
                    f"{cell.coef_raw} ({cell.stars} star{'s' * (cell.stars != 1)})",
                    f"{rep_stars} star{'s' * (rep_stars != 1)}",
                    "Significance level differs — check standard errors / clustering.")
                ok = False
            matched += ok

    # A variable-wide diagnosis needs evidence from every model that reports the variable.
    appearances = Counter(cell.variable.lower() for col in paper.columns for cell in col.cells)
    tolerance = Decimal(str(rel_tol))
    for name, columns in scale_samples.items():
        if len(columns) < 2 or len(columns) != appearances[name]:
            continue
        values = columns.values()
        ratios = [Decimal(str(q)) / Decimal(str(cell.coef)) for cell, q in values]
        low, high = min(ratios), max(ratios)
        if low <= 0 or high > low * (1 + tolerance):
            continue
        if low <= 1 + tolerance and high >= 1 - tolerance:
            continue
        factor = sum(ratios) / len(ratios)
        variable = next(iter(values))[0].variable
        add(", ".join(columns), variable, "cross_column_scale", "major" if abs(factor - 1) > MAJOR_REL else "minor",
            ", ".join(cell.coef_raw for cell, _ in values), ", ".join(f"{q:.4g}" for _, q in values),
            f"Across these models the replicated coefficients are about {factor:.4g} times the paper values. "
            f"Check the units and scaling of {variable}.")
    return ComparisonReport(paper.label, total, matched, out, paper.unverified_numbers())
