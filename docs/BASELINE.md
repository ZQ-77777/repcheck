# Baseline comparison: raw chatbot vs. RepCheck

Task D3 (OPERATION_GUIDE 7.2). **Method note:** we do not have ChatGPT/Claude web accounts on
this machine, so the baseline is simulated via the HKUST GenAI API: a raw model receives the
full paper text (35 pages, each tagged with its page number) plus the plain question, with none
of RepCheck's page selection, field templates, quote requirements or verification. Two models:

- `gpt-4.1-mini` — stands in for "ask ChatGPT" (same model family as the ChatGPT product);
- `deepseek/deepseek-v4-flash-0731` — the model RepCheck itself uses, asked without the
  pipeline: a clean ablation showing what the pipeline adds on top of the same model.

Question (identical for both, transcripts in `examples/outputs/baseline/`):

> I want to replicate Table 3 of this paper. List the sample period, data sources, sample
> filters, unit of observation, dependent variable, key independent variables, controls, fixed
> effects, standard errors, estimation method and winsorization, with page numbers.

## Per-item scoring against the gold checklist (`examples/gold/jw2020_table3_gold.json`)

| Item | gpt-4.1-mini (raw) | deepseek-v4-flash (raw) | RepCheck (same deepseek) |
|---|---|---|---|
| Sample period | correct (p.8) | correct (p.8) | correct, quote verified |
| Data sources | correct (p.8) | correct (p.8) | correct, quote verified |
| Sample filters | correct (p.8) | correct (p.8) | correct, quote verified |
| Unit of observation | correct (p.8) | correct (p.8) | correct, quote verified |
| Dependent variable | correct (p.8) | correct (p.8) | correct, quote verified |
| Key independent vars | correct | correct (p.14) | correct, quote verified |
| Controls | mostly correct, but falsely claims MKTRET and CAR_PRE are "not in Table 3" — both are printed in every column of the table (p.14) | correct (p.14) | correct, quote verified |
| Fixed effects | correct | correct (p.14) | correct, quote verified |
| Standard errors | correct | correct (p.14) | correct, quote verified |
| Estimation method | correct | correct ("implied", no page) | correct, quote verified |
| Winsorization | **invented** — the paper never mentions it; the model suggests "standard practice … 1% or 0.5% tails" and falsely claims the paper "mentions winsorization in other contexts" | **correct** — "not mentioned" (though it adds the unprovable "no winsorization is applied") | **correct** — flagged *missing / not in paper*; no value is produced |

Both baselines were asked about 11 items; RepCheck's fixed template covers all 13 fields
(the baselines do not systematically report subsamples/column structure or the sample size,
though both mention the spread split in passing).

## Summary (the numbers for slide 9)

| | gpt-4.1-mini raw | deepseek raw | RepCheck (deepseek + pipeline) |
|---|---|---|---|
| Content items correct | 10/11 (controls right in part) | 11/11 | 12/12 (13 fields, 12 stated) |
| Invented (paper silent, model answers anyway) | **1** | 0 | **0** — unreported fields are marked *not in paper* |
| Factual slips inside "correct" answers | 1 (MKTRET/CAR_PRE claimed absent from Table 3) | 0 | n/a — every claim carries a verified quote |
| Quotes to verify any answer | 0 | 0 | 17/17 for this table, verified by program (26/26 on Table 2) |
| Page numbers | given for all items, correct (a few cite adjacent pages, e.g. "8-9" for p.8) | given, all correct (journal pagination) | given, verified/corrected by program |

## Reading

- A long-context model given the whole paper gets most items right in a single pass — the
  content gap is small. The visible failure modes are **filling silence** and **unchecked
  detail**: gpt-4.1-mini answers the winsorization question with "standard practice" and even
  asserts the paper mentions it (the paper never does), and it confidently claims two control
  variables are absent from Table 3 while they are printed in every column — errors a user
  cannot catch without redoing the search themselves.
- The deeper gap is **verifiability**: neither baseline offers a single verbatim quote, so a
  user cannot check any answer against the paper without redoing the search themselves. Every
  RepCheck item carries quotes that the program fuzzy-matches against the PDF, and page
  numbers that are corrected or flagged automatically.
- **Stability:** the same deepseek model, in the same live run, declined to infer the
  estimation method for Table 2 (paper never names OLS) yet volunteered it for Table 3 —
  unprompted behaviour varies across calls; the fixed template plus missing-detection makes
  the output structure identical every run.
- Fairness note: the baselines received *more* text than RepCheck ever sends (all 35 pages
  vs. at most 8 selected pages) and still lose on verifiability and hallucination control.
