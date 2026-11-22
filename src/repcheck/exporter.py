"""M6 — Exports.

checklist_to_markdown / checklist_to_json : the reviewed checklist (allowed any time;
                                            pending items are clearly marked)
render_skeleton                           : code skeleton, ONLY from reviewed checklists
report_to_markdown                        : stage-2 comparison report
The skeleton is rendered from a Jinja2 template; the model never writes code.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .review import require_ready
from .schemas import Checklist, ChecklistItem, ComparisonReport, ReviewStatus

TEMPLATE_DIR = Path(__file__).parent / "templates"
STATUS_ICON = {"verified": "✅ verified", "unverified": "⚠️ unverified", "missing": "❌ missing"}
FE_TOKENS = ("firm", "year", "industry", "country", "quarter", "month", "state", "day")


# ----------------------------------------------------------------------------- checklist
def _fmt(value) -> str:
    if value is None:
        return "—"
    return "<br>".join(f"• {v}" for v in value) if isinstance(value, list) else str(value)


def _evidence(item: ChecklistItem) -> str:
    if not item.evidence:
        return "—"
    return "<br>".join(f"p.{e.page}{' (corrected)' if e.page_corrected else ''}"
                       f"{'' if e.verified else ' ⚠️'}: “{e.quote}”" for e in item.evidence)


def checklist_to_markdown(c: Checklist) -> str:
    lines = [f"# Replication checklist — {c.table.label}", "",
             f"- Paper: {c.paper_title or c.source_file}",
             f"- Table: {c.table.caption} (PDF page {', '.join(map(str, c.table.pages))})",
             f"- Model: {c.model_name} · template: {c.template} · exported {datetime.now():%Y-%m-%d %H:%M}",
             f"- Review complete: {'yes' if c.ready_to_export() else 'NO — pending items remain'}", "",
             "| Field | Extracted value | Evidence | Check | Review | Final value |",
             "|---|---|---|---|---|---|"]
    for i in c.items:
        final = i.final_value()
        if i.review_status == ReviewStatus.NOT_IN_PAPER:
            final = "Not reported in paper"
        note = f"<br>Note: {i.user_note}" if i.user_note else ""
        hint = f"<br>*{i.hint}*" if i.hint else ""
        lines.append(f"| {i.label}{' *' if i.required else ''} | {_fmt(i.value)} | {_evidence(i)} | "
                     f"{STATUS_ICON[i.extraction_status.value]}{hint} | {i.review_status.value}{note} | "
                     f"{_fmt(final)} |".replace("\n", " "))
    lines += ["", "\\* required field"]
    return "\n".join(lines) + "\n"


def checklist_to_json(c: Checklist) -> str:
    return json.dumps(c.to_dict(), ensure_ascii=False, indent=2)


# ------------------------------------------------------------------------------ skeleton
def _ident(name: str) -> str:
    s = re.sub(r"\W+", "_", name.strip()).strip("_")
    return s if s and not s[0].isdigit() else f"v_{s}"


def split_var(entry: str) -> tuple[str, str]:
    """'LEV: (DLTT + DLC) / AT' -> ('LEV', '(DLTT + DLC) / AT')."""
    if ":" in entry:
        name, definition = entry.split(":", 1)
    else:
        name, definition = (entry.split()[0] if entry.split() else "VAR"), entry
    return _ident(name), definition.strip()


def _as_list(v) -> list[str]:
    return [] if v is None else (v if isinstance(v, list) else [v])


def _where(item: ChecklistItem | None) -> str:
    pages = sorted({e.page for e in item.evidence}) if item else []
    return f" (p.{', p.'.join(map(str, pages))})" if pages else ""


def _winsor(value) -> dict:
    if value is None:
        return {"lower": 0.01, "upper": 0.99,
                "comment": "TODO: winsorization not confirmed — defaults shown, check the paper"}
    text = " ".join(_as_list(value))
    nums = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*(?:st|nd|rd|th|%|percent)", text)]
    if len(nums) >= 2:
        lo, hi = min(nums), max(nums)
        return {"lower": round(lo / 100, 4), "upper": round(hi / 100, 4), "comment": f"Paper: {text}"}
    if len(nums) == 1:
        p = nums[0] / 100
        return {"lower": p, "upper": round(1 - p, 4), "comment": f"Paper: {text}"}
    return {"lower": 0.01, "upper": 0.99, "comment": f"TODO: could not parse '{text}' — defaults shown"}


def _vcov(text: str | None) -> tuple[str, str]:
    if not text:
        return '"iid"', "TODO: standard errors not confirmed"
    low = text.lower()
    if "cluster" in low:
        dims = [t for t in FE_TOKENS if t in low]
        if dims:
            return repr({"CRV1": "+".join(dims)}), text
    if any(k in low for k in ("robust", "heterosk", "heterosc", "white")):
        return '"hetero"', text
    return '"iid"', f"{text}  -> TODO: map to a pyfixest vcov option"


def skeleton_context(c: Checklist) -> dict:
    get = lambda k: c.get(k).final_value() if c.get(k) else None  # noqa: E731
    period = get("sample_period")
    years = re.findall(r"\b(?:19|20)\d{2}\b", " ".join(_as_list(period)))
    dep = [split_var(e) for e in _as_list(get("dependent_var"))]
    keys = [split_var(e) for e in _as_list(get("key_independent_vars"))]
    ctrls = [split_var(e) for e in _as_list(get("controls"))]
    variables, seen = [], set()
    for name, definition in dep + keys + ctrls:
        if name not in seen:
            seen.add(name)
            variables.append({"name": name, "definition": definition})

    fe_text = " ".join(_as_list(get("fixed_effects")))
    low = re.sub(r"year[\s-]quarter", "year_quarter", fe_text.lower())   # one FE, not year + quarter
    fe = [t for t in FE_TOKENS if t in low.replace("year_quarter", "")]
    fe += ["year_quarter"] if "year_quarter" in low else []
    lhs = dep[0][0] if dep else "Y_TODO"
    rhs = " + ".join(n for n, _ in keys + ctrls) or "X_TODO"
    formula = f"{lhs} ~ {rhs}" + (f" | {' + '.join(fe)}" if fe else "")
    se_text = " ".join(_as_list(get("standard_errors"))) or None
    vcov, se_comment = _vcov(se_text)
    model = " ".join(_as_list(get("model")))
    model_comment = model or "TODO: estimation method not confirmed"
    if model and not re.search(r"\bols\b|least squares|linear", model.lower()):
        model_comment += "  -> TODO: feols is OLS; use pf.feglm/other estimator"

    def block(key, is_list=True):
        v = get(key)
        if v is None:
            return None
        return {"entries": _as_list(v), "where": _where(c.get(key))} if is_list else \
               {"text": " ".join(_as_list(v)), "where": _where(c.get(key))}

    return {
        "table_label": c.table.label, "paper_title": c.paper_title, "source_file": c.source_file,
        "sample_period": None if period is None else {
            "text": " ".join(_as_list(period)), "where": _where(c.get("sample_period")),
            "start": years[0] if years else "None", "end": years[-1] if years else "None",
            "todo": len(years) < 2},
        "unit": block("unit_of_observation", is_list=False),
        "data_sources": block("data_sources"), "filters": block("sample_filters"),
        "not_in_paper": [i.label for i in c.items if i.review_status == ReviewStatus.NOT_IN_PAPER],
        "wins": _winsor(get("winsorization")), "variables": variables, "formula": formula,
        "vcov": vcov, "se_comment": se_comment, "model_comment": model_comment,
        "fe_comment": fe_text or "TODO: fixed effects not confirmed",
        "subsamples_comment": " ".join(_as_list(get("subsamples"))) or "same sample in every column (not confirmed otherwise)",
    }


def render_skeleton(c: Checklist) -> str:
    require_ready(c)
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), undefined=StrictUndefined,
                      keep_trailing_newline=True, autoescape=False)
    return env.get_template("skeleton.py.j2").render(**skeleton_context(c))


# -------------------------------------------------------------------------------- report
KIND_ORDER = ["column_missing", "n_mismatch", "variable_missing", "sign_flip", "scale", "cross_column_scale",
              "magnitude", "significance", "se_mismatch"]
KIND_TITLES = {
    "column_missing": "Missing columns", "n_mismatch": "Sample size differs",
    "variable_missing": "Variables missing from the replication", "sign_flip": "Opposite signs",
    "scale": "Units / scaling differ", "magnitude": "Coefficient magnitudes differ",
    "cross_column_scale": "Consistent scaling across models",
    "significance": "Significance levels differ",
    "se_mismatch": "Standard errors differ",
}

def report_to_markdown(r: ComparisonReport) -> str:
    lines = [f"# Replication check — {r.table_label}", "",
             f"**Overall: {r.overall}** · {r.matched_cells}/{r.total_cells} coefficients match "
             f"(sign, magnitude and significance)", ""]
    if r.unverified_paper_numbers:
        lines += ["⚠️ These paper numbers could not be verified on the table page "
                  "(possible transcription error — check before trusting the comparison): "
                  + ", ".join(r.unverified_paper_numbers), ""]
    if not r.discrepancies:
        return "\n".join(lines + ["No discrepancies found."]) + "\n"
    lines += ["| Column | Variable | Type | Severity | Paper | Replication | What it suggests |",
              "|---|---|---|---|---|---|---|"]
    for d in r.discrepancies:
        lines.append(f"| {d.column} | {d.variable or '—'} | {d.kind} | {d.severity} | {d.paper or '—'} | "
                     f"{d.replicated or '—'} | {d.message} |")
    lines += ["", "## Where to look first", ""]
    for kind in KIND_ORDER:
        group = [d for d in r.discrepancies if d.kind == kind]
        if not group:
            continue
        if kind == "cross_column_scale":
            location = "across model columns"
        else:
            where = sorted({d.column for d in group})
            location = f"in column{'s' * (len(where) > 1)} {', '.join(where)}"
        lines.append(f"**{KIND_TITLES[kind]}** ({len(group)}× {location}) — re-check:")
        notes = list(dict.fromkeys(n for d in group for n in d.suspect_notes)) or \
            [f"`{k}`" for k in group[0].suspects]
        lines += [f"- {n}" for n in notes]
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
