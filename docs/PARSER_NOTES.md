# Parser and table locator notes

Owner: member B — `pdf_parser.py`, `table_locator.py`, `text_utils.py`.
Last updated: 2026-11-21.

This note records what the parser and the table locator do on **real** journal PDFs, what broke, and
what is still not supported. The private papers themselves are not in the repository (copyright);
every number below can be reproduced with the commands in [section 4](#4-how-to-reproduce).

## TL;DR

| Question | Answer |
|---|---|
| Why was JW2020 Table 4 not found? | It is printed **sideways**: 95 % of the characters on that page are rotated 90°. pdfplumber's default extraction then returns one word or one character per line in reverse order, so the caption `Table 4` arrives as `4elbaT` and no caption line can be matched. |
| Fixed? | Yes. Sideways pages are re-flowed from character boxes along the text's own axes, one block per rotation angle (`pdf_parser.py`). JW2020 now lists Tables 1–6 and Table 4 is located on PDF p. 17 (printed p. 3870). |
| Other journals? | Three papers from the *AER*, *TAR* and *JFE*: **22/22 numbered tables** located, each on the page that carries the caption. None of those pages is rotated, so the fix does not change them. |
| Still not supported | Appendix / online-appendix labels (`Table A.1`, `Table D.7`, `Table OA2`), captions rendered as images, captions that do not start a line. See [section 5](#5-limitations-and-follow-ups). |

## 1. The JW2020 Table 4 case

### Symptom

Jayaraman & Wu (2020), *RFS* 33(8), published PDF, 35 pages. Before the fix:

```
$ python cli.py tables examples/private/jw2020.pdf
Table 1
Table 2
Table 3
Table 5
Table 6
```

Table 4 is visibly in the paper (the text on p. 16 says "Table 4 presents the results…"), and the
team's earlier runs had already noticed it. `TableNotFoundError` listed the other five tables.

### What the page actually contains

`python scripts/diagnose_table.py examples/private/jw2020.pdf --table 4` reported:

```
Rotated pages: p.17 (rotate 0, 95% sideways)
Caption-like lines for Table 4: 1
  p.16   score=-3  rejected (score not positive)
         'Table 4 presents the results based on three measures of accounting'
Prose mentions of Table 4: page(s) 16, 17
```

Page 17 carries text at **three different angles**:

| Angle | Characters | What it is |
|---|---|---|
| 90° | 1,535 | the table, its caption and its notes |
| 270° | 122 | the "Downloaded from academic.oup.com…" sidebar |
| 0° | 95 | the publisher's `[…] Page: 3870 3854–3888` banner |

pdfplumber's default `extract_text()` on that page starts like this:

```
TheReviewofFinancialStudies/v33n82020
[20:082/7/2020RFS-OP-REVF190138.tex] Page:3870 3854–3888
4elbaT
ecnamrofreperutuF
1+tIN
...
```

The caption is there, but reversed (`4elbaT`) and split into single characters, so `CAPTION_RE`,
which needs a line that starts with `Table <number>`, never matches. Nothing is wrong with the PDF
text layer — the word "Table 4" exists; only its reading order is lost.

### The fix

`pdf_parser._page_text` now checks, for every page, whether at least 30 % of the characters are not
upright. If so:

1. characters are grouped by their baseline angle (90°, 270°, 0° …);
2. each group is re-flowed on the table's own axes — project every character origin with
   `along = x·cosθ + y·sinθ` and `across = -x·sinθ + y·cosθ`, sort by `across` (highest first) then
   `along`, and rebuild the line;
3. the largest group (the table) is emitted first, the banner and sidebar after it.

Each angle has to be handled **separately**: a first attempt that re-flowed the whole page at the
modal angle (90°) produced `Table4n` — a letter from the upright banner was projected onto the
caption's baseline and broke the `\b` after the number, so the caption was still rejected. Grouping
by angle removes the interleaving.

Upright pages take the old code path unchanged; the fixture in `tests/fixtures/rotated_tables.pdf`
contains a page of each kind (rotated block + banner + sidebar, `/Rotate 90`, and an upright control
page), and `tests/test_parser_locator.py::RotatedTablePageTest` pins all of it.

### After

```
$ python cli.py tables examples/private/jw2020.pdf
Table 1
Table 2
Table 3
Table 4
Table 5
Table 6

$ python scripts/diagnose_table.py examples/private/jw2020.pdf --table 4
RESULT: found on page(s) [17]
  caption: 'Table4 Futureperformance'
  notes:   ''
  p.17: /Rotate=0, sideways characters 95%
```

The caption is run together (`Table4 Futureperformance`) because RFS prints that table without
inter-word spaces at this font size — the same tight-typesetting problem we already handle for
upright pages, and harmless for matching. Table pages for the other tables did not move (Table 3 is
still PDF p. 14, as in `examples/outputs/jw2020/table3/checklist.json`).

## 2. Tests on other journals

Three open-access copies of papers from three journals, each dropped in `examples/private/` and run
through `python cli.py tables` and `scripts/diagnose_table.py`. None of them has a rotated page; they
test the ordinary caption path on layouts we had not seen.

| Journal | Paper (version, pages) | Numbered tables | Found | Table checked | PDF page (printed page) | Observed |
|---|---|---|---|---|---|---|
| *AER* 116(10) | Cornelissen, Dustmann & Schönberg, "Knowledge Spillovers, Competition, and Individual Careers", 2026, 3910–3941 (published PDF, 32 pp.) | 10 | **10/10** | Table 3 | p. 18 (p. 3927) | Prose mention "Table 3 presents…" on p. 13 correctly scored −3 and ignored; Tables 3 and 4 share p. 18 and are told apart by their captions |
| *TAR* | Chen, Gao & Zeng, "Inequality Grows in Silence: The Impact of Newspaper Closures on CEO–Worker Pay Disparity", accepted version, 80 pp. | 8 | **8/8** | Table 2 | p. 48 (no printed numbers) | Tables sit at the end of the manuscript; earlier prose mentions ("Table 2 provides the results…", p. 22) are penalised; accepted version has no printed page numbers, so only the PDF index is available |
| *JFE* 186 | Berardi, Schaefer & Brown, "Do long-term yields help to estimate short-term risk premia?", 2026, art. 104386 (accepted copy, 24 pp.) | 4 | **4/4** | Table 3 | p. 12 (article number only) | Caption split over two lines (`Table 3` / title); the locator appends the next line and the caption is complete. No "Notes:" line on that table, so `TableTarget.notes` is empty |
| *RFS* 33(8) | Jayaraman & Wu (2020), published PDF, 35 pp. | 6 | **6/6** (after the fix) | Table 4 | p. 17 (p. 3870) | Sideways page, see section 1 |

Notes on the columns:

- "Found" counts the numbered tables the locator lists for that paper. Each located page was checked
  by eye against the caption on the page, not only by the returned page number.
- Printed page numbers are only available in the published *AER* PDF (the running head carries them).
  The accepted *TAR*/*JFE* copies have none, and *JFE* uses an article number instead of page numbers,
  so the tool always reports the **PDF page index** — which is also what the web app shows.
- The *AER* and *TAR* copies came from university repositories (Essex, White Rose) and the *JFE* copy
  from LBS Research Online; they are the accepted/published files of record, but only the *AER* one is
  the publisher's typeset version. They are not committed.

## 3. Failure modes and what the code does now

| Situation | Behaviour | Evidence |
|---|---|---|
| The page is printed sideways (rotated text block or `/Rotate`) | Re-flowed per rotation angle; caption recovered | JW2020 Table 4 |
| An upright banner / sidebar shares the rotated page | Re-flowed separately, appended after the table | JW2020 p. 17 (0° and 270° blocks) |
| Prose such as "Table 3 presents…" starts a line | Score −3, so the real caption wins; if nothing scores above 0 the table is reported missing | *AER* p. 13, *TAR* p. 22 |
| Caption and title on two lines | The next line is appended to the caption | *JFE* Table 3 |
| Caption spacing variants (`Table3`, `T able 3`, `T A B L E 3`, `TABLE II`) | Tolerated by `CAPTION_RE` | `test_caption_spacing_variants` |
| Table continues on the next page | `(continued)` pages are appended to the target | `test_continued_table_spans_pages` |
| No caption, but the running text mentions the table | `TableNotFoundError` now names those pages and suggests the diagnostic command | `test_missing_caption_points_to_the_prose_mention` |

## 4. How to reproduce

```bash
python -m pytest -q                                  # 60 tests, no API key, no private PDF
python cli.py tables examples/private/jw2020.pdf     # expects Tables 1-6
python scripts/diagnose_table.py examples/private/jw2020.pdf --table 4
python scripts/diagnose_table.py PAPER.pdf --table 3 # any paper
python scripts/make_fixtures.py                      # rebuild tests/fixtures/rotated_tables.pdf
```

`diagnose_table.py` exits 0 when the table is found and 1 when it is not, prints every caption-like
line with its score, the pages that mention the table in prose, and the orientation of those pages.
That is the first command to run when a table that is visibly present cannot be located.

## 5. Limitations and follow-ups

1. **Appendix and online-appendix labels are not supported.** `Table A.1`, `Table D.7`, `Table OA2`
   and `Table IA.1` are common in accounting and finance papers, and the locator ignores them because
   `parse_label` only accepts an integer or a Roman numeral. The *AER* paper has 7 such tables, the
   *TAR* paper 10, the *JFE* paper 4. Supporting them means widening `TableTarget.number` (a
   `schemas.py` change), which is why it is not in this PR.
2. **A caption rendered as an image cannot be found.** OCR is out of scope; the new error message and
   `diagnose_table.py` say so instead of silently returning "not found".
3. **Notes without a "Notes:" marker are not captured.** RFS table notes often start directly with
   "The dependent variable…", so `TableTarget.notes` is empty for all six JW2020 tables (including
   Table 4). The extractor still receives the table page itself, so this costs context, not evidence.
4. **Two tables on one page** (e.g. *AER* Tables 3 and 4 on p. 18) resolve to the same page. The
   caption is correct; the page alone cannot tell the two tables apart.
5. **Mixed-orientation pages below the 30 % threshold are left alone.** A page with only a small
   rotated block keeps the default extraction; this avoids mangling normal pages that happen to
   contain a few rotated annotations.
6. `scripts/run_examples.py` still fails loudly when `examples/private/jw2020.pdf` exists but is a
   *different file* from the one the demo cache was built from (the mock replay has no answer for its
   fingerprint). That is the documented "run once in live mode" case; the traceback could be a
   friendlier skip message.
