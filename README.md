# RepCheck: Evidence-Grounded Replication Specs and Result Checks

| Member | Student ID | Contribution |
|---|---|---|
| Zhang Qi | 21358199 | Design and v0.1 baseline; coordination and integration (`schemas.py`, `pipeline.py`, exporter); real-paper case study |
| TODO | TODO | TODO — PDF parsing and table locating; tests on further journals (`pdf_parser.py`, `table_locator.py`) |
| TODO | TODO | TODO — prompts, model comparison and stability tests (`extractor.py`, `llm/`) |
| TODO | TODO | TODO — gold annotations, evaluation, chatbot baseline, threshold study (`verifier.py`, `scripts/`) |
| TODO | TODO | TODO — Streamlit interface and review workflow (`app.py`) |
| TODO | TODO | TODO — result check and Stata import (`comparator.py`, `result_export.py`); lead presenter |

## User, task and role of AI

**User:** students and research assistants replicating a regression table from an empirical paper, and supervisors who check that work.

**Task:** (1) list everything needed to rebuild one table — sample, filters, variables, fixed effects, standard errors — each with page evidence, and say clearly what the paper does not report; (2) after replication, compare the results with the paper and point to the likely causes of any differences.

**Role of AI:** a language model does two narrow jobs: fill a fixed checklist from selected pages, quoting the paper verbatim, and transcribe the table's printed numbers. Our code does the rest: locating the table, selecting pages, checking every quote and number against the PDF text, flagging unreported items, requiring human review before export, rendering a code skeleton from a template, and diagnosing discrepancies.

## How to run

```bash
python -m venv .venv && source .venv/bin/activate      # Python 3.10+; Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py                    # Windows: or double-click run_app.bat
```

To check your own replication, export your fitted models with `src/repcheck/result_export.py` (statsmodels, linearmodels or pyfixest).

Without an API key the app runs in **mock mode**, replaying saved answers for the two example papers. For any other PDF, copy `.env.example` to `.env` and set `API_KEY`, `BASE_URL` and `MODEL` (any OpenAI-compatible chat API; we used the HKUST GenAI API service, see `.env.example`); answers are then cached in `examples/cache/`. No credentials are included.

```bash
python cli.py spec examples/inputs/e1_coverage_investment.pdf --table "Table 3"
python cli.py compare examples/inputs/e1_coverage_investment.pdf --table 3 --results examples/inputs/e1_replication_results.csv
python scripts/run_examples.py          # all examples, failure cases, evaluation
python cli.py doctor                    # check the setup (--ping also tests the API key)
python -m pytest -q                     # 45 tests incl. a headless UI test, no network or API key
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

Modules exchange data only through the dataclasses in `src/repcheck/schemas.py`. Model backends share one interface (live API or mock) and a caching wrapper. Checklist fields come from `checklist_templates.py`, so a new template (for example, machine-learning experiments) needs no changes elsewhere.

## Example results

Inputs, outputs and the full evaluation are in `examples/`.

| Input | Spec checklist | Result check |
|---|---|---|
| e1: synthetic paper, Table 3 | Paraphrased quote flagged; wrong page corrected | N −5%, ×100 scaling in CASH, missing ROA, misread SE caught |
| e2: synthetic paper, TABLE II | Clustering and winsorization reported as not in paper | 7/7 coefficients match |
| Real paper: Jayaraman & Wu (2020, *RFS*), Tables 2–3 | Table 3: 12/13 items with verified quotes, incl. the subsample rule; winsorization unreported. Fixing tightly typeset PDF text cut false alarms from 10 to 0 | Not run (shown on e1) |
| f1: scanned PDF | Clear error: no text layer | — |
| f2/f3: Table 9; malformed CSV | Lists available tables; names missing columns | — |

The real paper's PDF and data are not included (copyright and WRDS licence); its outputs are in `examples/outputs/jw2020/`. The e1/e2 runs use mock answers, so they test our pipeline rather than the model. TODO: add live-mode figures from `scripts/run_examples.py --mode live`.

**Helps:** shows where each detail is stated and what is missing, and turns a mismatch into a short list of pages to re-read. **Needs improvement:** tables printed as images cannot be read; cause suggestions are heuristics, not proof; only a regression-table template exists so far.

## Collaboration and handover lesson

TODO — one lesson from `docs/handover_log.md` (what made a teammate's module easy or hard to run or change).

## Credits

Libraries: pdfplumber, Jinja2, Streamlit, python-dotenv, rapidfuzz; generated skeletons use pyfixest. Claude (Anthropic) drafted the initial v0.1 code, tests and documentation; TODO — describe what the team changed and other AI tools used. Example papers are fictional and generated by `scripts/make_examples.py`; mock answers in `examples/cache/` are hand-written fixtures.
