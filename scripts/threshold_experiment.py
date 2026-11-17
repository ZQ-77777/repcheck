"""Measure how the verifier's MATCH_THRESHOLD trades false rejects against false accepts.

    python scripts/threshold_experiment.py [--thresholds 80 85 90 95]

Three quote sets are compared against the PDFs with the production verify_evidence():
  * true        — every verified quote in the cached checklists (examples/outputs/*/checklist.json);
                  the text really is in the PDF, so these should be accepted;
  * paraphrased — hand-written rewordings of sentences from the same PDFs (plus the one
                  reworded quote the e1 mock fixture already contains); too lenient a
                  threshold accepts them;
  * invented    — plausible sentences that appear in neither PDF; they must be rejected.

Writes docs/threshold_results.md and prints the table.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from repcheck.pipeline import load_paper          # noqa: E402
from repcheck.schemas import Evidence             # noqa: E402
from repcheck.verifier import verify_evidence     # noqa: E402

E1 = ROOT / "examples/inputs/e1_coverage_investment.pdf"
E2 = ROOT / "examples/inputs/e2_board_payout.pdf"

# Hand-written rewordings of sentences that do appear in the PDFs.
PARAPHRASED = [
    (E1, 2, "Our sample spans fiscal years 2003 to 2019."),
    (E1, 2, "Financial firms (SIC 6000-6999) and utilities (SIC 4900-4999) are excluded from the sample."),
    (E1, 2, "Observations are at the firm-year level."),
    (E1, 2, "We require non-missing regression variables and lagged total assets exceeding $10 million."),
    (E1, 3, "Standard errors are clustered by firm."),
    (E1, 3, "All models are estimated by OLS."),
    (E1, 3, "Firm and year fixed effects are included in every specification."),
    (E2, 2, "The sample period is 2005 to 2018."),
    (E2, 2, "Accounting data are from Compustat and board data from BoardEx."),
    (E2, 2, "Firms must have non-missing board data and positive total assets."),
    (E2, 4, "PAYOUT is dividends (DVC) over income before extraordinary items (IB)."),
    # Reworded quote already shipped in the e1 mock fixture ("1st and 99th percentiles"
    # became "1% and 99% to remove outliers"); kept as a natural paraphrase sample.
    (E1, 2, "All continuous variables are winsorized at 1% and 99% to remove outliers."),
]

# Plausible sentences that appear in neither PDF.
INVENTED = [
    (E1, 2, "All variables are winsorized at the 1st and 99th percentiles of their annual distributions to mitigate outliers."),
    (E1, 3, "Standard errors are clustered at the industry level."),
    (E1, 3, "All regressions include firm and quarter fixed effects."),
    (E1, 2, "The sample excludes firms with fewer than five analysts."),
    (E1, 2, "We use quarterly data from 2010 to 2020."),
    (E2, 2, "Board independence data come from RiskMetrics."),
    (E2, 2, "The final sample contains 15,000 firm-year observations."),
    (E2, 2, "We also run tests with winsorized and trimmed samples."),
]


def collect_true() -> list[tuple[Path, int, str]]:
    """Verified quotes from every cached checklist whose PDF is available locally."""
    out = []
    for checklist_path in sorted((ROOT / "examples/outputs").glob("*/checklist.json")):
        data = json.loads(checklist_path.read_text(encoding="utf-8"))
        pdf = ROOT / "examples/private" / data["source_file"] if data["source_file"].startswith("../") \
            else ROOT / "examples/inputs" / data["source_file"]
        pdf = pdf.resolve()
        if not pdf.exists():
            continue
        for item in data["items"]:
            for e in item["evidence"]:
                if e["verified"]:
                    out.append((pdf, e["page"], e["quote"]))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--thresholds", nargs="+", type=float, default=[80, 85, 90, 95])
    args = ap.parse_args()

    true_quotes = collect_true()
    papers: dict[Path, dict[int, str]] = {}
    for pdf in {q[0] for q in true_quotes + PARAPHRASED + INVENTED}:
        papers[pdf] = {p.number: p.text for p in load_paper(pdf).pages}

    def accepted(quotes, threshold) -> int:
        return sum(verify_evidence(Evidence(page, quote), papers[pdf], threshold).verified
                   for pdf, page, quote in quotes)

    rows = ["| Threshold | True quotes accepted | False rejects | Paraphrased accepted | "
            "Invented accepted |", "|---|---|---|---|---|"]
    for t in args.thresholds:
        ok = accepted(true_quotes, t)
        rows.append(f"| {t:g} | {ok}/{len(true_quotes)} | {len(true_quotes) - ok} | "
                    f"{accepted(PARAPHRASED, t)}/{len(PARAPHRASED)} | "
                    f"{accepted(INVENTED, t)}/{len(INVENTED)} |")
    table = "\n".join(rows)
    print(table)
    (ROOT / "docs/threshold_results.md").write_text(
        "# Match-threshold experiment\n\nSee `scripts/threshold_experiment.py`. "
        f"Quote sets: {len(true_quotes)} true, {len(PARAPHRASED)} paraphrased, "
        f"{len(INVENTED)} invented.\n\n{table}\n", encoding="utf-8")
    print(f"\nWrote docs/threshold_results.md")


if __name__ == "__main__":
    main()
