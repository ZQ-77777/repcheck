# Design notes

Problems we had to solve, and how the code solves them. File names point to the implementation.

## Stage 1 — specification checklist

| Problem | Solution | Where |
|---|---|---|
| Prose such as "Table 3 reports…" also starts lines; the real caption must win | Score caption candidates: title-like text, digit-dense page, "This table…/Notes" on the page; prose verbs are penalised. Arabic and Roman numerals; "(continued)" pages appended | `table_locator.py` |
| Whole papers are too long and noisy for the model | Send at most 8 pages: the table pages always, then pages ranked by checklist keywords, the table's variable names, and a bonus for variable-definition appendices | `retriever.py` |
| Models invent details and page numbers | Every field must carry verbatim quotes; each quote is fuzzy-matched (≥90) against its page, then against all pages (page corrected). Unmatched → `unverified` | `verifier.py`, `text_utils.py` |
| Models fill gaps with "common practice" | A fixed template lists every field; anything not returned is `missing`. Hints come from our keyword index, never from the model | `checklist_templates.py`, `verifier.py` |
| Users must stay in control | Each item needs a decision (confirm / edit / reject / not in paper). Code export is blocked until all required items are decided | `review.py`, `app.py` |
| Generated code must be predictable | Jinja2 template filled only with reviewed values; everything else is an explicit TODO. The model never writes code | `exporter.py`, `templates/skeleton.py.j2` |
| TA or teammates may have no API key; demos must not depend on the network | Provider interface with live and mock implementations; a caching wrapper stores every live answer, which mock mode replays | `llm/` |
| PDF text quirks (ligatures, hyphenation, Unicode minus) break matching | One shared normalisation used by every comparison | `text_utils.py` |

## Stage 2 — result check

| Problem | Solution | Where |
|---|---|---|
| The paper's numbers must be read reliably | The model transcribes the table; every printed string (coefficient, SE/t, N) must appear verbatim on the table page, sign included. Unverified numbers are listed in the report | `table_numbers.py` |
| Replication output comes in many forms | One simple long CSV format (`column, variable, coef, se, pvalue, n`); labels "1" and "(1)" are equivalent | `comparator.py` |
| A mismatch alone does not tell the RA what to fix | Each discrepancy type maps to checklist items to re-check, shown with the confirmed value and its page: N gap → filters/period/sources; sign flip or ×100 → variable definitions; magnitude → winsorization/controls; significance → standard errors | `comparator.py` (`SUSPECTS`) |
| t-statistics vs standard errors | Paper stars are read from the printed coefficient; replication stars from p-values or coef/SE | `comparator.py` |

## Interfaces

All modules exchange the dataclasses in `schemas.py`: `Page`, `TableTarget`, `Context`, `Evidence`, `ChecklistItem`, `Checklist`, `PaperTable`, `ResultRow`, `Discrepancy`, `ComparisonReport`. `pipeline.py` is the only module that calls the others in sequence; `app.py` and `cli.py` call `pipeline.py`.

## Choosing the match threshold (90)

`verifier.py` accepts a quote when its fuzzy score against the PDF text reaches `MATCH_THRESHOLD`. We measured the trade-off with three quote sets (`scripts/threshold_experiment.py`, raw table in `docs/threshold_results.md`):

- **true** (70): every verified quote from the cached e1/e2 checklists plus the 43 verified quotes from the live JW2020 runs — the text is in the PDF, so these should be accepted;
- **paraphrased** (12): hand-written rewordings of real sentences (swapping synonyms, passive voice, dropping words), plus the reworded winsorization quote that already ships in the e1 mock fixture;
- **invented** (8): plausible sentences that appear in neither PDF (e.g. "clustered at the industry level" where the paper says firm level).

| Threshold | True accepted | False rejects | Paraphrased accepted | Invented accepted |
|---|---|---|---|---|
| 80 | 70/70 | 0 | 5/12 | 2/8 |
| 85 | 70/70 | 0 | 4/12 | 2/8 |
| 90 | 70/70 | 0 | 1/12 | 0/8 |
| 95 | 70/70 | 0 | 1/12 | 0/8 |

Reading:

- At 80–85 the verifier accepts two invented quotes. Both are the dangerous kind: a single keyword swapped against a real sentence ("winsorized at the 1st and 99th percentiles…", "clustered at the industry level"), scoring 85.7 and 88.5. A lenient threshold would wave through exactly the hallucinations the verifier exists to catch.
- At 90 all invented quotes are rejected and 11 of 12 paraphrases. The one that passes (95.4) changes only two words ("We require firms to have…" → "Firms must have…") — close enough that a human reviewer can confirm it quickly; the item is still shown for review anyway.
- The true quotes score between 98.9 and 100 — the live JW2020 quotes, transcribed by the model from a PDF with tight typesetting, still come out near-verbatim. All pass at 90 with room to spare. We keep 90 rather than 95 because the two thresholds behave identically on these sets while 90 leaves a larger safety margin for noisier PDF extraction (missing spaces, ligatures) or a different model; the e1 winsorization paraphrase scoring 80.8 shows the kind of model rewording the threshold must catch.

## Known limitations

- Tables printed as images, and scanned PDFs, are rejected rather than OCR'd.
- Page numbers are PDF page indices, not printed page numbers.
- Cause suggestions are heuristics; they rank where to look, they do not prove a cause.
- The skeleton models one specification (all confirmed variables); other columns are left to the user.
- Only the `regression` template exists; structural-estimation or ML papers need their own templates.
