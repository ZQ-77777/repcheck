# Contributions

Each member keeps their own section up to date. Link pull requests or commits. The README table and the
peer ratings are based on this file.

## Baseline (5 Nov 2026)
- v0.1 code, tests, synthetic examples and documents were drafted by Zhang Qi with AI assistance (Claude,
  Anthropic) as a starting point. Each module then has an owner who reviews, tests and extends it.

## Zhang Qi (A, 21358199) — design, coordination and integration
- Chose the topic and designed the two-stage tool (specification checklist, then result check), the
  module pipeline and the shared interfaces in `schemas.py`; built the v0.1 baseline with tests,
  synthetic examples, mock mode and the HKUST GenAI API connection (header and temperature handling).
- Set up the repository (CI workflow, PR template, `.gitattributes`), split the work into six roles,
  wrote the team guides and timeline, reviewed and merged pull requests, and integrated releases.
- Real-paper case study (Jayaraman & Wu 2020): found and fixed run-together words in tightly typeset
  PDFs (false quote alarms 10 → 0 on Tables 2–3); added the "Subsamples / column structure" field after
  the paper showed it was missing; drafted the Table 3 gold answers from the paper text for D to verify.
- Final integration before submission: README, slides and demo runbook; demo fixes (edited items stay
  open in the interface; a year-quarter fixed effect is one term in the code skeleton, with a test).
- Handover H2: handed the live demo to Zhou Zhenyu (`docs/handover_log.md`).

### AI usage statement (Zhang Qi)
- I used Claude (Anthropic) as a coding and writing assistant. It drafted the v0.1 baseline code,
  tests and synthetic example papers, the later fixes listed above, the README, the slides and the
  team guides. I set the design and scope, ran everything on my own Windows machine and on the real
  paper, decided what to keep, and checked every reported number against the program's output.
  Model answers used in the project come from the HKUST GenAI API; the copyrighted paper PDF stays
  local and is never committed.

## Tang Yunshu (B, 21275921) — PDF parsing and table locating
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
  270° sidebar, a `/Rotate 90` page and an upright control) and 5 new tests (64 in the suite after PR #5 merged, all passing).
- Pull requests: #6

### AI usage statement (Tang Yunshu)
- For the PDF-parsing and table-locating part I used an AI coding assistant (DeepSeek Harness) as a pair programmer. It implemented the per-angle re-flow in pdf_parser.py, generated the synthetic rotated-page fixture, drafted the five new tests and produced the first draft of docs/PARSER_NOTES.md. I set the task, supplied the published JW2020 PDF and verified every claim against the actual pages: the before/after cli.py tables output, the page of Table 4 (PDF p. 17, printed p. 3870) and the 22/22 table count for the AER, TAR and JFE papers all come from running the code, not from the model. All AI-written code and prose were read, executed and edited before the pull request, and the copyrighted paper PDF stays local and is never committed.

## Xinyi Dou (21357339) — prompts and model comparison

- Ran the sequential comparison of GPT-4.1 mini, DeepSeek V4 Flash and DeepSeek V4 Pro on JW2020 Tables 2 and 3, with three planned attempts per model and table and separate caches for each attempt. Recorded completion status, elapsed time and API balance changes.
- Compared repeated outputs to identify changes in answers and evidence. Evaluated the optional v2 prompt requesting explicit units, scaling and standardization details.
- Produced the English model comparison report and slide data, including runtime, estimated cost, automatic quote matching, reference-answer scores and a recommendation to retain Flash with v1 as the default.
- Used D's reference answers to score the 34 successful checklists across v1 and v2, and rechecked the scores and quote statuses after B's parser update.
- Pull requests: #1, #8.

### AI usage statement

I used OpenAI Codex to help prepare experiment commands, draft the optional v2 prompt, compare saved outputs, run the reference-answer scoring and tests, and draft and revise the report, slide data and contribution record. Codex also compared standardization statements and their supporting quotes with the PDF and rechecked compatibility after B's parser update. I ran the model experiments, supplied the terminal results and API balance readings, reviewed the report, questioned the scoring criteria and interpretation of the results, and requested revisions. The reference-answer scores use the project's automatic word-overlap evaluator. Codex assisted with checks against the PDF and the interpretation of output differences.


## Xu Fanqi (D, 21355721) — evaluation and baseline
- Wrote the JW2020 gold answers against the published RFS PDF, independently of the drafter:
  `jw2020_table2_gold.json` from scratch (all 13 fields, including the Model 1-8 column
  structure and the 3,456-forecast SF_CAR subsample) and line-by-line verification of
  `jw2020_table3_gold.json` — resolved both CHECK items ("Model 9 of Table 2" is a numbering
  slip in the paper; LAG_CAPX is scaled in the regressions but in US$ millions in Table 1).
- Ran the live evaluation (`run_examples.py --mode live`, deepseek-v4-flash): JW2020 Table 3
  12/12 fields, 17/17 quotes verified; Table 2 10/12 with both misses explainable and
  documented (`examples/outputs/evaluation.md`).
- Match-threshold experiment justifying `MATCH_THRESHOLD = 90`
  (`scripts/threshold_experiment.py`, new section in `docs/DESIGN.md`, 3 new tests): 83 true
  quotes (27 fixtures + 56 live across JW2020 and the NBER handover paper) all accepted at 90,
  while 80-85 accept invented quotes that swap a single keyword.
- Baseline comparison for slide 9 (`scripts/baseline_experiment.py`, `docs/BASELINE.md`):
  raw gpt-4.1-mini and raw deepseek given the full paper — content is mostly right but one
  invents the winsorization answer and neither offers a single verifiable quote.
- Handover H1: ran the full evaluation on an unseen paper (NBER WP 32161) using only B's module
  docstring and tests, then re-checked after B's rotated-page fix landed (no regression; JW2020
  Table 4 confirmed found).
- Pull requests: #3, #4, #7

### AI usage statement (Xu Fanqi)
- For the evaluation and baseline part I used an AI coding assistant (CodeBuddy, GLM) as a pair
  programmer. It drafted the two experiment scripts (`scripts/threshold_experiment.py`,
  `scripts/baseline_experiment.py`), assembled the hand-written paraphrase and invented quote
  sets, produced the first drafts of `docs/BASELINE.md`, `docs/DESIGN.md` (threshold section),
  `docs/EVALUATION_GUIDE.md` and my CONTRIBUTIONS entry, and fixed two path-handling bugs it had
  introduced in the threshold script. I supplied the published JW2020 PDF, wrote and verified
  every field of the two gold answers against the paper (all 33 factual citations were checked
  programmatically against the stated PDF pages), scored both baseline transcripts item by item
  against the gold, re-ran every number after teammates' PRs merged, and read, executed and
  edited everything before opening each pull request. All reported figures come from running
  the code, not from the model, and the copyrighted paper PDF stays local and is never committed.

## Du Yunhe (E, 21419400) — web interface, handover and install test
- Added a "Show source text" panel under every evidence quote in `app.py`: ~200 characters of the
  page text around the matched span with the match highlighted, located by a new `quote_context`
  helper in `text_utils.py` that reuses the verifier's normalization (hyphen joins, lost word
  spaces, curly quotes), so the UI always shows the same span the check accepted. An off-by-one in
  the window slicing was caught by the new unit tests before it reached the UI.
- Added "Continue review" to `app.py`: uploading a previously exported `checklist.json` restores
  decisions, notes and the review gate through `Checklist.from_dict`, and a paper-fingerprint
  mismatch (`content_hash`) shows a visible warning instead of silently applying one paper's
  confirmed values to another. Widget keys are versioned so restored decisions are not overwritten
  by stale radio state.
- Handover H3 (2026-11-22): installed and ran the project following only `README.md` in a fresh
  venv, and documented two README bugs in `docs/handover_log.md` — `python -m venv` does not exist
  on a stock Mac, and pytest is missing from the documented install step. Fixed both in the README
  and resolved the committed merge-conflict markers in `docs/handover_log.md`.
- 6 unit tests for `quote_context` and 4 headless UI tests; 75 tests in the suite after the
  changes, all passing. Changes are delivered as files for A to merge (no direct push):
  `app.py`, `src/repcheck/text_utils.py`, `tests/test_app_ui.py`, `tests/test_text_utils.py`,
  `README.md`, `docs/handover_log.md`, this file.

### AI usage statement (Du Yunhe)
- WorkBuddy produced the bulk of the code: the `quote_context` helper, both `app.py`
  features, the ten tests, my `docs/handover_log.md` entry and the first draft of this paragraph.
  My contribution was the spec and the verification. I required up front that the viewer locate
  quotes through the verifier's own normalization within ~200 characters, that a fingerprint
  mismatch stop and warn instead of applying silently, and that restored decisions survive a
  re-render — then checked each behavior myself. Every number comes from actual runs: 75 tests
  from `pytest -q`, the restore and warning flows from headless AppTest runs, and the two README
  problems from a fresh-venv install guided only by the README.

## Zhou Zhenyu (F,21358187) — result check, presentation and live demo
- Added `convert_esttab_csv` in `result_export.py`: converts Stata `esttab` output (standard errors in
  parentheses) to the results CSV, with tests and `examples/inputs/f_esttab_sample.csv`.
- Added two diagnosis rules in `comparator.py`: standard errors that differ by more than 25%
  (points to clustering) and coefficients scaled by the same factor across all models (points to units).
- Lead presenter and live demo; final slides.
