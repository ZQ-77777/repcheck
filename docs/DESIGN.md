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

## Known limitations

- Tables printed as images, and scanned PDFs, are rejected rather than OCR'd.
- Page numbers are PDF page indices, not printed page numbers.
- Cause suggestions are heuristics; they rank where to look, they do not prove a cause.
- The skeleton models one specification (all confirmed variables); other columns are left to the user.
- Only the `regression` template exists; structural-estimation or ML papers need their own templates.
