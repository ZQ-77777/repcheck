"""Run every example input, the failure cases, and the evaluation against the gold checklists.

    python scripts/run_examples.py [--mode mock|live]

Writes examples/outputs/<example>/... and examples/outputs/evaluation.md.
In mock mode the model answers come from examples/cache (see README): the numbers then
evaluate the deterministic pipeline, not the language model. Run with --mode live for
the real evaluation reported in the slides.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _utf8_console() -> None:
    """Chinese-locale Windows consoles use GBK and cannot print symbols such as ✅."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


_utf8_console()

from repcheck.comparator import ResultsFormatError, load_results_csv     # noqa: E402
from repcheck.exporter import (checklist_to_json, checklist_to_markdown,  # noqa: E402
                               report_to_markdown)
from repcheck.llm import get_provider                                    # noqa: E402
from repcheck.pdf_parser import ScannedPDFError                          # noqa: E402
from repcheck.pipeline import load_paper, run_compare, run_spec          # noqa: E402
from repcheck.schemas import ExtractionStatus                            # noqa: E402
from repcheck.table_locator import TableNotFoundError                    # noqa: E402

INPUTS, GOLD, OUT = ROOT / "examples/inputs", ROOT / "examples/gold", ROOT / "examples/outputs"
PRIVATE = ROOT / "examples/private"     # real papers: kept out of git and the submission ZIP
EXAMPLES = [  # (id, pdf, table, results csv, gold, output folder); paths relative to examples/inputs
    ("e1", "e1_coverage_investment.pdf", "Table 3", "e1_replication_results.csv", "e1_gold.json",
     "e1_coverage_investment"),
    ("e2", "e2_board_payout.pdf", "TABLE II", "e2_replication_results.csv", "e2_gold.json", "e2_board_payout"),
    # Real-paper case study: skipped automatically when the PDF, results or gold file is absent.
    ("jw2020-t2", "../private/jw2020.pdf", "Table 2", "jw2020_table2_results.csv", "jw2020_table2_gold.json",
     "jw2020/table2"),
    ("jw2020-t3", "../private/jw2020.pdf", "Table 3", "jw2020_table3_results.csv", "jw2020_table3_gold.json",
     "jw2020/table3"),
]
FAILURES = [  # (id, description, callable)
    ("f1", "Scanned PDF (no text layer)", lambda prov: load_paper(INPUTS / "f1_scanned.pdf")),
    ("f2", "Table that does not exist (Table 9 in e1)",
     lambda prov: run_spec(load_paper(INPUTS / "e1_coverage_investment.pdf"), "Table 9", prov)),
    ("f3", "Results CSV with wrong columns", lambda prov: load_results_csv(INPUTS / "f2_bad_results.csv")),
]
STOP = {"the", "of", "and", "a", "an", "in", "for", "to", "by", "at", "with", "from", "is", "are", "all"}
MATCH = 0.6


def tokens(v) -> set[str]:
    text = " ".join(v) if isinstance(v, list) else str(v or "")
    text = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", text.lower())     # 1st -> 1, 99th -> 99
    return {t for t in re.findall(r"[a-z0-9$]+", text) if t not in STOP}


def overlap(gold, system) -> float:
    """Share of the shorter answer's tokens found in the other (lenient on wording)."""
    g, s = tokens(gold), tokens(system)
    return len(g & s) / min(len(g), len(s)) if g and s else 0.0


def evaluate(checklist, gold: dict) -> dict:
    r = {"correct": 0, "wrong": 0, "missed": 0, "true_missing": 0, "hallucinated": 0,
         "quotes": 0, "verified_quotes": 0, "flagged": 0, "rows": []}
    for item in checklist.items:
        g = gold["fields"].get(item.key)
        found = item.extraction_status != ExtractionStatus.MISSING
        r["quotes"] += len(item.evidence)
        r["verified_quotes"] += sum(e.verified for e in item.evidence)
        r["flagged"] += item.extraction_status == ExtractionStatus.UNVERIFIED
        if g is None:
            outcome = "hallucinated" if found else "true_missing"
        elif not found:
            outcome = "missed"
        else:
            outcome = "correct" if overlap(g, item.value) >= MATCH else "wrong"
        r[outcome] += 1
        r["rows"].append((item.label, item.extraction_status.value, outcome))
    return r


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["mock", "live"], default="mock")
    mode = ap.parse_args().mode
    prov = get_provider(mode)
    lines = [f"# Evaluation ({mode} mode)", ""]
    if mode == "mock":
        lines += ["> Mock mode replays hand-written fixtures in examples/cache. These figures test the "
                  "deterministic pipeline (locating, verification, missing detection, comparison), "
                  "**not** the language model. Re-run with `--mode live` for model results.", ""]
    else:
        lines += ["> Live mode calls the API only for (PDF, table) pairs without a cached answer; cached "
                  "pairs are replayed unchanged. The e1/e2 rows therefore still replay the hand-written "
                  "fixtures in examples/cache (deterministic pipeline); the jw2020 rows are real model "
                  "answers.", ""]
    lines += ["| Example | Fields correct | Wrong | Missed | Unreported → flagged missing | Invented | "
              "Quotes verified | Flagged for review | Result check |", "|---|---|---|---|---|---|---|---|---|"]
    details = []
    for ex_id, pdf, table, csv_name, gold_name, out_name in EXAMPLES:
        needed = [INPUTS / pdf, GOLD / gold_name]          # the results CSV is optional (stage 2)
        if not all(p.exists() for p in needed):
            missing = ", ".join(p.name for p in needed if not p.exists())
            print(f"{ex_id}: skipped (missing {missing})")
            continue
        out = OUT / out_name
        out.mkdir(parents=True, exist_ok=True)
        paper = load_paper(INPUTS / pdf)
        checklist = run_spec(paper, table, prov)
        (out / "checklist.json").write_text(checklist_to_json(checklist), encoding="utf-8")
        (out / "checklist.md").write_text(checklist_to_markdown(checklist), encoding="utf-8")
        result_check = "not run (no results CSV)"
        if (INPUTS / csv_name).exists():
            _, report = run_compare(paper, table, INPUTS / csv_name, prov, checklist)
            (out / "comparison.md").write_text(report_to_markdown(report), encoding="utf-8")
            (out / "comparison.json").write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
                                                 encoding="utf-8")
            result_check = (f"{report.overall}: {report.matched_cells}/{report.total_cells} coef. match, "
                            f"{len(report.discrepancies)} issues")
        gold = json.loads((GOLD / gold_name).read_text(encoding="utf-8"))
        e = evaluate(checklist, gold)
        n_gold = sum(v is not None for v in gold["fields"].values())
        n_null = len(gold["fields"]) - n_gold
        lines.append(f"| {ex_id} | {e['correct']}/{n_gold} | {e['wrong']} | {e['missed']} | "
                     f"{e['true_missing']}/{n_null} | {e['hallucinated']} | "
                     f"{e['verified_quotes']}/{e['quotes']} | {e['flagged']} | {result_check} |")
        details.append(f"\n### {ex_id}: {Path(pdf).name}, {table}\n\n| Field | Check | Outcome vs gold |\n|---|---|---|")
        details += [f"| {a} | {b} | {c} |" for a, b, c in e["rows"]]
        print(f"{ex_id}: {e['correct']}/{n_gold} correct; result check {result_check}")

    lines += ["", "## Failure cases", "", "| Case | Input | Behaviour |", "|---|---|---|"]
    for f_id, desc, fn in FAILURES:
        try:
            fn(prov)
            behaviour = "❌ no error raised (unexpected)"
        except (ScannedPDFError, TableNotFoundError, ResultsFormatError) as exc:
            behaviour = f"✅ {type(exc).__name__}: {exc}"
        lines.append(f"| {f_id} | {desc} | {behaviour} |")
        print(f"{f_id}: {behaviour[:90]}")
    (OUT / "evaluation.md").write_text("\n".join(lines + ["", "## Per-field detail"] + details) + "\n",
                                       encoding="utf-8")
    print(f"Wrote {OUT / 'evaluation.md'}")


if __name__ == "__main__":
    main()
