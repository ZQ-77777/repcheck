# Contributions

Each member keeps their own section up to date. Link pull requests or commits. The README table and the
peer ratings are based on this file.

## Baseline (5 Nov 2026)
- v0.1 code, tests, synthetic examples and documents were drafted by Zhang Qi with AI assistance (Claude,
  Anthropic) as a starting point. Each module then has an owner who reviews, tests and extends it.

## Zhang Qi — coordination and integration
- Design of the two-stage tool and the interfaces in `schemas.py`; integration and releases.
- Real-paper case study (Jayaraman & Wu 2020): fixed run-together words in tightly typeset PDFs
  (false quote alarms 10 → 0 on Tables 2–3); added the "Subsamples / column structure" field after the
  paper showed it was missing; connected the HKUST GenAI API.
- Pull requests:

## Member B — PDF parsing and table locating
- Root-caused the missing JW2020 Table 4: the page is printed sideways (95% of its characters are
  rotated 90°), so pdfplumber returned the caption reversed as `4elbaT` and no caption line matched.
  Sideways pages are now re-flowed from character boxes, one block per rotation angle, in
  `pdf_parser.py` (a naive single-angle re-flow was not enough: the upright publisher banner merged
  into the caption line). JW2020 now lists Tables 1–6; Table 4 resolves to PDF p. 17 (printed p. 3870).
- Tested the locator on three further journal papers (*AER*, *TAR*, *JFE*; 22/22 numbered tables
  located) and recorded versions, page mapping and remaining gaps in `docs/PARSER_NOTES.md`.
- `TableNotFoundError` now reports the pages that mention a table in prose, so an image caption can be
  told apart from a typo; added `scripts/diagnose_table.py` to explain any missing table in one command.
- Added `scripts/make_fixtures.py` with `tests/fixtures/rotated_tables.pdf` (rotated block + banner +
  270° sidebar, a `/Rotate 90` page and an upright control) and 5 new tests (60 total, all passing).
- Pull requests: #6

## Xinyi Dou (Member C) — prompts and model comparison
- Ran the sequential comparison of three models on JW2020 Tables 2 and 3 and analyzed the stability of the extracted answers and evidence.
- Added an optional v2 extraction prompt and compared runtime, estimated cost, quote matching and coverage of standardization details.
- Wrote the model comparison report. Field accuracy is pending review against the reference answers.

## Member D — evaluation and baseline
- Wrote the JW2020 gold answers against the published RFS PDF, independently of the drafter:
  `jw2020_table2_gold.json` from scratch (all 13 fields, including the Model 1-8 column
  structure and the 3,456-forecast SF_CAR subsample) and line-by-line verification of
  `jw2020_table3_gold.json` — resolved both CHECK items ("Model 9 of Table 2" is a numbering
  slip in the paper; LAG_CAPX is scaled in the regressions but in US$ millions in Table 1).
- Ran the live evaluation (`run_examples.py --mode live`, deepseek-v4-flash): JW2020 Table 3
  12/12 fields, 17/17 quotes verified; Table 2 10/12 with both misses explainable and
  documented (`examples/outputs/evaluation.md`).
- Match-threshold experiment justifying `MATCH_THRESHOLD = 90`
  (`scripts/threshold_experiment.py`, new section in `docs/DESIGN.md`, 3 new tests): 70 true
  quotes (27 fixtures + 43 live) all accepted at 90, while 80-85 accept invented quotes that
  swap a single keyword.
- Baseline comparison for slide 9 (`scripts/baseline_experiment.py`, `docs/BASELINE.md`):
  raw gpt-4.1-mini and raw deepseek given the full paper — content is mostly right but one
  invents the winsorization answer and neither offers a single verifiable quote.
- Pull requests: #3

## Member E — interface
- Pull requests:

## Member F — result check and presentation
- Pull requests:
