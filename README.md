# RepCheck: Evidence-Grounded Replication Specs and Result Checks

| Member | Contribution |
|---|---|
| Zhang Qi | Design and v0.1 baseline; integration (`schemas.py`, `pipeline.py`, exporter); real-paper case study: tight-typesetting fix, subsample field, HKUST GenAI API |
| Tang Yunshu | Sideways (rotated) table pages in `pdf_parser.py`; locator tested on *AER*, *TAR* and *JFE* papers; `diagnose_table.py` |
| Dou Xinyi | Three-model comparison and stability study; optional v2 prompt (`docs/MODEL_COMPARISON.md`) |
| Xu Fanqi | JW2020 gold answers; live evaluation; match-threshold study; chatbot baseline; handover test on an unseen paper |
| Du Yunhe | Integration and debugging; cross-checked the paper facts and page references used in our examples and slides |
| Zhou Zhenyu | Stata `esttab` import (`convert_esttab_csv`); two result-check rules (standard-error gaps, consistent scaling across models); lead presenter and live demo |

## User, task and role of AI

**User:** students and research assistants replicating a regression table from an empirical paper, and supervisors who check that work.

**Task:** (1) list everything needed to rebuild one table, each item with page evidence, and say clearly what the paper does not report; (2) after replication, compare the results with the paper and point to likely causes of differences.

**Role of AI:** a language model does two narrow jobs: fill a fixed checklist from selected pages, quoting the paper verbatim, and transcribe the table's printed numbers. Our code does the rest: locating the table, selecting pages, checking every quote and number against the PDF text, flagging unreported items, requiring human review before export, rendering a code skeleton from a template, and diagnosing discrepancies.

## How to run

```bash
python -m venv .venv && source .venv/bin/activate      # Python 3.10+; Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py                    # Windows: or double-click run_app.bat
```

To check your own replication, export fitted models with `src/repcheck/result_export.py` (statsmodels, linearmodels, pyfixest) or convert Stata `esttab` output with `convert_esttab_csv`.

Without an API key the app runs in **mock mode**, replaying saved answers. For other PDFs, copy `.env.example` to `.env` and set `API_KEY`, `BASE_URL` and `MODEL` (any OpenAI-compatible chat API); answers are cached in `examples/cache/`. No credentials are included.

```bash
python cli.py spec examples/inputs/e1_coverage_investment.pdf --table "Table 3"
python cli.py compare examples/inputs/e1_coverage_investment.pdf --table 3 --results examples/inputs/e1_replication_results.csv
python scripts/run_examples.py          # all examples, failure cases, evaluation
python cli.py doctor                    # check the setup (--ping also tests the API key)
python -m pytest -q                     # 65 tests incl. a headless UI test, no network or API key
```

## Architecture

```
PDF + "Table 3"
  → pdf_parser → table_locator → retriever ──► extractor (LLM) ──► verifier → Checklist
                                                                      │  human review (app.py / review.py)
                                                                      ▼
                                                    exporter: checklist.md/json, skeleton.py
results.csv + PDF → extractor (LLM) → table_numbers (verify) → comparator → report.md
```

Modules exchange data only through the dataclasses in `src/repcheck/schemas.py`. Model backends share one interface (live or mock) plus a caching wrapper. Checklist fields come from `checklist_templates.py`, so a new template needs no other changes.

## Example results

Inputs, outputs and the full evaluation (`examples/outputs/evaluation.md`) are in `examples/`. Real papers ran live on DeepSeek V4 Flash (`docs/MODEL_COMPARISON.md`).

| Input | Spec checklist | Result check |
|---|---|---|
| Real paper: Jayaraman & Wu (2020, *RFS*), Tables 2–3 | Table 3: 12/12 stated items correct against our gold answers, 17/17 quotes verified, winsorization correctly reported as absent. Table 2: 10/12, 26/26 quotes | Not run (shown on e1) |
| Unseen paper: NBER WP 32161, Table 2 (handover test) | Found among 17 tables; 11/13 items with verified quotes | — |
| e1: synthetic paper, Table 3 | Paraphrased quote flagged; wrong page corrected | N −5%, ×100 scaling, missing ROA, misread SE caught |
| e2: synthetic paper, TABLE II | Clustering and winsorization reported as not in paper | 7/7 coefficients match |
| f1–f3: scanned PDF; Table 9; malformed CSV | Clear errors: no text layer; lists tables found; names missing columns | — |

Real-paper PDFs are excluded (copyright); e1/e2 replay hand-written answers to test the pipeline.

**Helps:** every item comes with a quote checked against the PDF. Given the whole paper, GPT-4.1 mini got 10/11 items right but invented a winsorization rule and offered no verifiable quote (`docs/BASELINE.md`). The quote threshold of 90 accepted 83/83 true quotes and 0/8 invented ones (`docs/DESIGN.md`). **Needs improvement:** scanned PDFs, image captions and appendix labels (Table A.1) are not read; the model's wording varies between runs; the word-overlap score can pass incomplete answers; cause suggestions are heuristics.

## Collaboration and handover lesson

Xu Fanqi ran the whole tool on an NBER paper it had never seen, using only the docstrings and tests of the table-locating module owned by Tang Yunshu, in about 15 minutes. The docstring states input, output and errors, and the tests work as a usage manual; deciding whether a missing field is truly unreported still needed a person (`docs/handover_log.md`).

## Credits

Libraries: pdfplumber, Jinja2, Streamlit, python-dotenv, rapidfuzz; generated skeletons use pyfixest. Models via the HKUST GenAI API: DeepSeek V4 Flash (default), DeepSeek V4 Pro and GPT-4.1 mini (comparison and baseline). AI assistance: Zhang Qi drafted the v0.1 baseline with Claude (Anthropic); Tang Yunshu used DeepSeek Harness as a pair programmer for the sideways-table parser. All AI-written code was reviewed, run and tested by the team (`docs/CONTRIBUTIONS.md`). Synthetic papers are generated by `scripts/make_examples.py`; NBER WP 32161 is open access.
