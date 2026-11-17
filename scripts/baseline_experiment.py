"""Baseline: ask a raw model the replication question with the full paper, no RepCheck pipeline.

    python scripts/baseline_experiment.py [--model gpt-4.1-mini] [--table Table 3]

Simulates "upload the paper to ChatGPT/Claude and ask" (OPERATION_GUIDE 7.2): the model gets
the whole paper text with page markers and the plain question — none of RepCheck's page
selection, field templates, quote requirements or verification. Answers are saved to
examples/outputs/baseline/<model>_<table>.md for manual scoring against the gold checklist
(docs/BASELINE.md). Caches under examples/cache_exp/baseline/ so demo caches stay untouched.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

QUESTION = ("I want to replicate Table 3 of this paper. List the sample period, data sources, "
            "sample filters, unit of observation, dependent variable, key independent variables, "
            "controls, fixed effects, standard errors, estimation method and winsorization, "
            "with page numbers.")

PDF = ROOT / "examples" / "private" / "jw2020.pdf"
OUT = ROOT / "examples" / "outputs" / "baseline"
CACHE = ROOT / "examples" / "cache_exp" / "baseline"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.getenv("MODEL", "gpt-4.1-mini"))
    args = ap.parse_args()

    from repcheck.llm import get_provider
    from repcheck.pdf_parser import parse_pdf

    pages = parse_pdf(PDF)
    paper = "\n\n".join(f"[Page {p.number}]\n{p.text}" for p in pages)
    user = QUESTION.replace("Table 3", "Table 3") + "\n\nThe paper follows.\n\n" + paper

    os.environ["MODEL"] = args.model          # picked up when the provider is constructed
    prov = get_provider("live", CACHE)
    key = "baseline_" + re.sub(r"[^a-z0-9]+", "", args.model.lower()) + "_table3"
    answer = prov.complete("You are a helpful assistant.", user, key)

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{key}.md"
    out.write_text(f"# Baseline: {args.model}, Table 3\n\n## Question\n\n{QUESTION}\n\n"
                   f"## Answer (raw model, full paper in context)\n\n{answer}\n", encoding="utf-8")
    print(f"model: {prov.name}\nsaved: {out}")


if __name__ == "__main__":
    main()
